import boto3

# ------------------------
# Variables (Change Here)
# ------------------------
REGION = "ap-south-1"
VPC_CIDR = "10.0.0.0/16"
SUBNET_CIDR = "10.0.1.0/24"
KEY_PAIR_NAME = "thiru"          # existing key pair
INSTANCE_TYPE = "t2.micro"
AMI_ID = "ami-02b8269d5e85954ef"   # Ubuntu 22.04 LTS (for ap-south-1)
TAG_NAME = "Apache-Server"
# ------------------------

ec2 = boto3.resource("ec2", region_name=REGION)
client = boto3.client("ec2", region_name=REGION)

# Create VPC
vpc = ec2.create_vpc(CidrBlock=VPC_CIDR)
vpc.create_tags(Tags=[{"Key": "Name", "Value": "Custom-VPC"}])
vpc.wait_until_available()

print("Created VPC:", vpc.id)

# Create Internet Gateway and attach to VPC
igw = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=igw.id)
print("Attached Internet Gateway:", igw.id)

# Create Route Table & Route
route_table = vpc.create_route_table()
route_table.create_route(DestinationCidrBlock="0.0.0.0/0", GatewayId=igw.id)
print("Created Route Table:", route_table.id)

# Create Subnet
AVAILABILITY_ZONE = "ap-south-1a"   # choose valid AZ manually

subnet = ec2.create_subnet(
    CidrBlock=SUBNET_CIDR,
    VpcId=vpc.id,
    AvailabilityZone=AVAILABILITY_ZONE
)

print("Created Subnet:", subnet.id)

# Associate subnet with route table
route_table.associate_with_subnet(SubnetId=subnet.id)

# Create Security Group
security_group = ec2.create_security_group(
    GroupName="Apache-SG",
    Description="Security group for Apache Web Server",
    VpcId=vpc.id
)
print("Created Security Group:", security_group.id)

# Authorize Inbound Rules using client
client.authorize_security_group_ingress(
    GroupId=security_group.id,
    IpPermissions=[
        {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
         "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
         "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
    ]
)
print("Ingress rules added successfully")

with open("apache2.sh", "r") as file:
    USER_DATA_SCRIPT = file.read()

# Create EC2 Instance
instance = ec2.create_instances(
    ImageId=AMI_ID,
    InstanceType=INSTANCE_TYPE,
    KeyName=KEY_PAIR_NAME,
    MaxCount=1,
    MinCount=1,
    NetworkInterfaces=[{
        "DeviceIndex": 0,
        "SubnetId": subnet.id,
        "AssociatePublicIpAddress": True,
        "Groups": [security_group.id]
    }],
    UserData=USER_DATA_SCRIPT,
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [{'Key': 'Name', 'Value': TAG_NAME}]
    }]
)[0]

instance.wait_until_running()
instance.reload()

print("EC2 Instance Created Successfully!")
print("Instance ID:", instance.id)
print("Public IP:", instance.public_ip_address)
print("Access Apache at: http://{}/".format(instance.public_ip_address))
