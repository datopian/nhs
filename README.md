# nhs

CKAN data portal for NHS

## List the contents of an Amazon S3 bucket and create a datapackage.json

This function gets a list of all available resources in the Amazon s3 bucket, lists them, and creates a datapacakge.json. The datapackage.json contains information about the files.

Credentials needed:

`
ckanext.nhs.aws_access_key_id = XXXXX
ckanext.nhs.aws_secret_access_key = YYYYY
ckanext.nhs.bucket_name = bucket_name
`

Structure of the datapackage.json:

```
{
  "name": "name-is-required",
  "resources": [
    {
      "title": "File title 1",
      "path": "path",
      "publisher": "publisher",  // not sure if it's supported
      "size": file_size,
     "format": "..."
    }
  ]
}
```
