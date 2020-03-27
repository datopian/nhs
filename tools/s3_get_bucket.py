"""    
Extract data from S3 at http://nhsbsa-opendata.s3-eu-west-2.amazonaws.com/
Analyze the folder called DATOPIAN_DATA (http://nhsbsa-opendata.s3-eu-west-2.amazonaws.com/DATOPIAN_DATA/)

an aws_access_key_id & aws_secret_access_key are required to be authenticated in S3
"""


import boto3

s3 = boto3.resource('s3',
                    aws_access_key_id='XXXXXX',
                    aws_secret_access_key='XXXXXXXXX')
# requires to install aws cli.
# response = s3.list_buckets()

bucket_name = 'nhsbsa-opendata'

response = s3.buckets.all()
# print('Existing buckets:')

# for bucket in s3.buckets.all():
#    print (bucket.name)

for my_bucket in response:
    bn = my_bucket.name

    if bn == bucket_name:
        print('******* BUCKET ***********')
        print(f'  {bn}')
        print('**************************')
        for my_bucket_object in my_bucket.objects.all():
            print(my_bucket_object)


