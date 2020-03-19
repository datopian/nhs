"""    
Extract data from S3 at http://nhsbsa-opendata.s3-eu-west-2.amazonaws.com/
Analyze the folder called DATOPIAN_DATA (http://nhsbsa-opendata.s3-eu-west-2.amazonaws.com/DATOPIAN_DATA/)
"""


import boto3

s3 = boto3.client('s3')
# requires to install aws cli.
response = s3.list_buckets()

print('Existing buckets:')
for bucket in response['Buckets']:
    bn = bucket["Name"]
    
    
    if bn == 'nhsbsa-opendata':
        c = 0
        print('******* BUCKET ***********')
        print(f'  {bn}')
        print('**************************')
        for key in s3.list_objects(Bucket=bn)['Contents']:
            name = key['Key']
            """
            {'Key': 'DATOPIAN_DATA/DPI_DETAIL_PRESCRIBING_201912.zip',
             'LastModified': datetime.datetime(2020, 3, 16, 20, 46, 7, tzinfo=tzutc()),
             'ETag': '"nnnnnn"',
             'Size': 496039759,
             'StorageClass': 'STANDARD'}
            """
            size = key['Size'] / 1000000
            print(f"     {name}: {size} MB")
            c += 1
        print(f'We have {c} files')
    

