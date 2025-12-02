import boto3

def create_vpc_resources():

    ec2 = boto3.resource('ec2')
    client = boto3.client('ec2')

    # 1. Create VPC
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc.wait_until_available()
    vpc.create_tags(Tags=[{"Key": "Name", "Value": "MyVPC"}])
    print("VPC Created:", vpc.id)

    # 2. Create Internet Gateway
    igw = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=igw.id)
    igw.create_tags(Tags=[{"Key": "Name", "Value": "MyIGW"}])
    print("Internet Gateway Created:", igw.id)

    # 3. Create Route Table & Route
    route_table = vpc.create_route_table()
    route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=igw.id
    )
    print("Route Table Created:", route_table.id)

    # 4. Create Subnet
    subnet = ec2.create_subnet(
        CidrBlock="10.0.1.0/24",
        VpcId=vpc.id,
        AvailabilityZone="ap-soth-1a"
    )
    subnet.create_tags(Tags=[{"Key": "Name", "Value": "MySubnet"}])
    print("Subnet Created:", subnet.id)

    # Associate subnet with route table
    route_table.associate_with_subnet(SubnetId=subnet.id)

    # 5. Create Security Group
    sg = ec2.create_security_group(
        GroupName="MySG",
        Description="Allow SSH and HTTP",
        VpcId=vpc.id
    )
    sg.create_tags(Tags=[{"Key": "Name", "Value": "MySG"}])

    # Add rules
    sg.authorize_security_group_ingress(
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22, 'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 80, 'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print("Security Group Created:", sg.id)

    return vpc, subnet, sg


def create_ec2_instance(subnet_id, sg_id):
    ec2 = boto3.resource('ec2')

    instance = ec2.create_instances(
        ImageId='ami-02b8269d5e85954ef', 
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.micro',
        KeyName='thiru',  
        SecurityGroupIds=[sg_id],
        SubnetId=subnet_id,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': 'MyEC2Instance'}]
            }
        ]
    )

    print(f"EC2 Instance Created: {instance[0].id}")


if __name__ == "__main__":
    vpc, subnet, sg = create_vpc_resources()
    create_ec2_instance(subnet.id, sg.id)
