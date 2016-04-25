import argparse
import boto
import boto.s3.key
import os


def progress_cb(curr, total):
    print('%d / %d B (%.2f%%)') % (curr, total, curr * 100.0 / float(total))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('upload a file to S3')
    parser.add_argument('file', help='path to the local file to upload')
    parser.add_argument('bucket', help='name of the S3 bucket to upload into')

    args = parser.parse_args()

    bucket = boto.connect_s3().get_bucket(args.bucket)
    key = boto.s3.key.Key(bucket=bucket, name=os.path.basename(args.file))
    key.set_contents_from_filename(args.file, cb=progress_cb, num_cb=20)
