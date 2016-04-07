import boto
import boto.s3.connection
from boto.s3.key import Key
import sys

class S3Service():

    def __init__(self, s3_secret_key, s3_access_key):
        self.s3_secret_key = s3_secret_key
        self.s3_access_key = s3_access_key
        self.conn = boto.connect_s3(
            aws_access_key_id=self.s3_secret_key,
            aws_secret_access_key=self.s3_access_key)

    def uploadFileToS3(self, bucket, key_name, file_path):
        k = Key(bucket)
        k.key = key_name
        k.set_contents_from_filename(file_path,
                                     cb=self.percent_cb, num_cb=10)
        return k

    def percent_cb(complete, total, somethingElse):
        sys.stdout.write('.')
        sys.stdout.flush()