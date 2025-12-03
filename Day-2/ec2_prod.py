import boto3

REGION = "ap-south-1"
VPC_NAME = "Custom-VPC"
SUBNET_NAME = "Custom-Subnet"
SG_NAME = "Apache-SG"

ec2 = boto3.resource("ec2", region_name=REGION)
client = boto3.client("ec2", region_name=REGION)

# ----------------------- CHECK & CREATE VPC -----------------------
vpcs = list(ec2.vpcs.filter(
    Filters=[{"Name": "tag:Name", "Values": [VPC_NAME]}]
))

if vpcs:
    vpc = vpcs[0]
    print("Existing VPC found:", vpc.id)
else:
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    vpc.create_tags(Tags=[{"Key": "Name", "Value": VPC_NAME}])
    vpc.wait_until_available()
    print("Created new VPC:", vpc.id)

# ----------------------- CHECK & CREATE SUBNET -----------------------
subnets = list(vpc.subnets.filter(
    Filters=[{"Name": "tag:Name", "Values": [SUBNET_NAME]}]
))

if subnets:
    subnet = subnets[0]
    print("Existing Subnet found:", subnet.id)
else:
    subnet = ec2.create_subnet(CidrBlock="10.0.3.0/24", VpcId=vpc.id, AvailabilityZone="ap-south-1a")
    subnet.create_tags(Tags=[{"Key": "Name", "Value": SUBNET_NAME}])
    print("Created new Subnet:", subnet.id)

# ----------------------- CHECK & CREATE SECURITY GROUP -----------------------
sg_list = client.describe_security_groups(
    Filters=[
        {"Name": "group-name", "Values": [SG_NAME]},
        {"Name": "vpc-id", "Values": [vpc.id]}
    ]
)

if sg_list["SecurityGroups"]:
    sg_id = sg_list["SecurityGroups"][0]["GroupId"]
    print("Existing Security Group found:", sg_id)
else:
    sg = ec2.create_security_group(
        GroupName=SG_NAME,
        Description="SG for Apache web server",
        VpcId=vpc.id
    )
    sg_id = sg.id
    print("Created new Security Group:", sg_id)

    client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
        ]
    )
    print("Ingress rules added.")

# ----------------------- READ USER DATA FILE -----------------------
with open("apache2.sh", "r") as f:
    user_data_script = f.read()

# ----------------------- CREATE EC2 INSTANCE -----------------------
instance = ec2.create_instances(
    ImageId="ami-02b8269d5e85954ef",
    InstanceType="t2.micro",
    KeyName="thiru",
    MinCount=1,
    MaxCount=1,
    NetworkInterfaces=[{
        "DeviceIndex": 0,
        "SubnetId": subnet.id,
        "AssociatePublicIpAddress": True,
        "Groups": [sg_id]
    }],
    UserData=user_data_script,
    TagSpecifications=[{
        "ResourceType": "instance",
        "Tags": [{"Key": "Name", "Value": "Apache-Server"}]
    }]
)[0]

instance.wait_until_running()
instance.reload()

print("Instance Running:", instance.id)
print("Public IP:", instance.public_ip_address)
#!/usr/bin/env python3
"""
Create (or reuse) a VPC, subnet, internet gateway, route table, security group,
and then launch an EC2 Ubuntu instance with Apache installed via user-data.

Requirements:
    - boto3 installed: pip install boto3
    - AWS credentials configured: aws configure
    - user-data script file: apache2.sh in the same directory
"""

import logging
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# ------------------------
# Configuration (edit as needed)
# ------------------------
REGION = "ap-south-1"
VPC_CIDR = "10.0.0.0/16"
SUBNET_CIDR = "10.0.1.0/24"
AVAILABILITY_ZONE = "ap-south-1a"  # must support chosen instance type

VPC_NAME = "Custom-VPC"
SUBNET_NAME = "Custom-Subnet"
ROUTE_TABLE_NAME = "Custom-RT"
SG_NAME = "Apache-SG"

KEY_PAIR_NAME = "thiru"          # existing key pair
INSTANCE_TYPE = "t2.micro"
AMI_ID = "ami-02b8269d5e85954ef"   # Ubuntu 22.04 LTS (for ap-south-1)
INSTANCE_TAG_NAME = "Apache-Server"

USER_DATA_FILE = "apache2.sh"
# ------------------------


# ---------- Logging setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------- Helper functions ----------
def get_boto3_clients(region: str):
    ec2_resource = boto3.resource("ec2", region_name=region)
    ec2_client = boto3.client("ec2", region_name=region)
    return ec2_resource, ec2_client


def get_or_create_vpc(ec2, cidr: str, name: str):
    vpcs = list(ec2.vpcs.filter(
        Filters=[{"Name": "tag:Name", "Values": [name]}]
    ))

    if vpcs:
        vpc = vpcs[0]
        logger.info(f"Reusing existing VPC: {vpc.id}")
        return vpc

    logger.info("No existing VPC found. Creating a new one...")
    vpc = ec2.create_vpc(CidrBlock=cidr)
    vpc.wait_until_available()
    vpc.create_tags(Tags=[{"Key": "Name", "Value": name}])
    logger.info(f"Created VPC: {vpc.id}")
    return vpc


def get_or_create_internet_gateway(ec2, vpc):
    # Check if IGW is already attached to this VPC
    client = boto3.client("ec2", region_name=REGION)
    igw_response = client.describe_internet_gateways(
        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc.id]}]
    )
    igws = igw_response.get("InternetGateways", [])

    if igws:
        igw_id = igws[0]["InternetGatewayId"]
        logger.info(f"Reusing existing Internet Gateway: {igw_id}")
        return ec2.InternetGateway(igw_id)

    logger.info("No existing Internet Gateway found. Creating a new one...")
    igw = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=igw.id)
    logger.info(f"Created and attached Internet Gateway: {igw.id}")
    return igw


def get_or_create_route_table(ec2, vpc, igw_id: str, name: str):
    route_tables = list(ec2.route_tables.filter(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc.id]},
            {"Name": "tag:Name", "Values": [name]},
        ]
    ))

    if route_tables:
        rt = route_tables[0]
        logger.info(f"Reusing existing Route Table: {rt.id}")
    else:
        logger.info("No existing Route Table found. Creating a new one...")
        rt = vpc.create_route_table()
        rt.create_tags(Tags=[{"Key": "Name", "Value": name}])
        logger.info(f"Created Route Table: {rt.id}")

    # Ensure route to Internet exists
    has_default_route = any(
        r.get("DestinationCidrBlock") == "0.0.0.0/0" and "GatewayId" in r
        for r in rt.routes_attribute
    )

    if not has_default_route:
        logger.info("Adding 0.0.0.0/0 route to Internet Gateway...")
        try:
            rt.create_route(DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
        except ClientError as e:
            if e.response["Error"]["Code"] != "RouteAlreadyExists":
                raise
        logger.info("Route added.")
    else:
        logger.info("Route to 0.0.0.0/0 already exists on this Route Table.")

    return rt


def get_or_create_subnet(ec2, vpc, cidr: str, az: str, name: str):
    subnets = list(vpc.subnets.filter(
        Filters=[
            {"Name": "tag:Name", "Values": [name]},
            {"Name": "availability-zone", "Values": [az]},
        ]
    ))

    if subnets:
        subnet = subnets[0]
        logger.info(f"Reusing existing Subnet: {subnet.id}")
        return subnet

    logger.info("No existing Subnet found. Creating a new one...")
    subnet = ec2.create_subnet(
        CidrBlock=cidr,
        VpcId=vpc.id,
        AvailabilityZone=az
    )
    subnet.create_tags(Tags=[{"Key": "Name", "Value": name}])
    logger.info(f"Created Subnet: {subnet.id}")
    return subnet


def associate_route_table_with_subnet(route_table, subnet):
    # Check if already associated
    for assoc in route_table.associations:
        if assoc.subnet_id == subnet.id:
            logger.info(f"Route Table {route_table.id} already associated with Subnet {subnet.id}")
            return
    logger.info(f"Associating Route Table {route_table.id} with Subnet {subnet.id}")
    route_table.associate_with_subnet(SubnetId=subnet.id)


def get_or_create_security_group(ec2, client, vpc, sg_name: str, description: str):
    try:
        response = client.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [sg_name]},
                {"Name": "vpc-id", "Values": [vpc.id]},
            ]
        )
        if response["SecurityGroups"]:
            sg_id = response["SecurityGroups"][0]["GroupId"]
            logger.info(f"Reusing existing Security Group: {sg_id}")
            return ec2.SecurityGroup(sg_id)
    except ClientError as e:
        if e.response["Error"]["Code"] != "InvalidGroup.NotFound":
            raise

    logger.info("No existing Security Group found. Creating a new one...")
    sg = ec2.create_security_group(
        GroupName=sg_name,
        Description=description,
        VpcId=vpc.id
    )
    logger.info(f"Created Security Group: {sg.id}")

    # Add ingress rules safely (idempotent-ish)
    try:
        client.authorize_security_group_ingress(
            GroupId=sg.id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
            ],
        )
        logger.info("Ingress rules (22, 80) added successfully.")
    except ClientError as e:
        # If rules already exist, ignore; otherwise re-raise
        if e.response["Error"]["Code"] != "InvalidPermission.Duplicate":
            raise
        logger.info("Ingress rules already exist; skipping.")

    return sg


def read_user_data_script(path: str) -> str:
    p = Path(path)
    if not p.exists():
        logger.error(f"User-data script file not found: {path}")
        sys.exit(1)

    content = p.read_text()
    if not content.strip().startswith("#!"):
        logger.warning(
            "User-data script does not start with a shebang (e.g., #!/bin/bash). "
            "EC2 will still run it, but it's best practice to add one."
        )
    return content


def create_ec2_instance(ec2, subnet, sg, ami_id, instance_type, key_name, user_data, tag_name):
    logger.info("Launching EC2 instance...")
    try:
        instances = ec2.create_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MaxCount=1,
            MinCount=1,
            NetworkInterfaces=[{
                "DeviceIndex": 0,
                "SubnetId": subnet.id,
                "AssociatePublicIpAddress": True,
                "Groups": [sg.id],
            }],
            UserData=user_data,
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": tag_name}],
            }],
        )
    except ClientError as e:
        logger.error(f"Failed to create EC2 instance: {e}")
        sys.exit(1)

    instance = instances[0]
    logger.info(f"Waiting for EC2 instance {instance.id} to enter 'running' state...")
    instance.wait_until_running()
    instance.reload()

    logger.info(f"EC2 Instance is running. ID: {instance.id}, Public IP: {instance.public_ip_address}")
    return instance


# ---------- Main ----------
def main():
    ec2, client = get_boto3_clients(REGION)

    try:
        vpc = get_or_create_vpc(ec2, VPC_CIDR, VPC_NAME)
        igw = get_or_create_internet_gateway(ec2, vpc)
        route_table = get_or_create_route_table(ec2, vpc, igw.id, ROUTE_TABLE_NAME)
        subnet = get_or_create_subnet(ec2, vpc, SUBNET_CIDR, AVAILABILITY_ZONE, SUBNET_NAME)
        associate_route_table_with_subnet(route_table, subnet)
        security_group = get_or_create_security_group(
            ec2, client, vpc, SG_NAME, "Security group for Apache Web Server"
        )
        user_data = read_user_data_script(USER_DATA_FILE)
        instance = create_ec2_instance(
            ec2, subnet, security_group, AMI_ID, INSTANCE_TYPE,
            KEY_PAIR_NAME, user_data, INSTANCE_TAG_NAME
        )

        logger.info("=== Summary ===")
        logger.info(f"VPC ID: {vpc.id}")
        logger.info(f"Subnet ID: {subnet.id}")
        logger.info(f"Security Group ID: {security_group.id}")
        logger.info(f"Instance ID: {instance.id}")
        logger.info(f"Apache URL: http://{instance.public_ip_address}/")

    except ClientError as e:
        logger.error(f"AWS ClientError occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
