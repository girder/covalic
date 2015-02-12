import boto


def get_bucket(bucket_name):
    # login with admin credentials
    conn = boto.connect_s3()

    # create a bucket if it doesn't exist
    bucket = conn.lookup(bucket_name)
    if not bucket:
        bucket = conn.create_bucket(bucket_name)

    return bucket

def set_bucket_policy(bucket):
    from boto.s3.cors import CORSConfiguration
    cors_cfg = CORSConfiguration()
    cors_cfg.add_rule(['PUT', 'POST', 'GET'], '*', allowed_header='*', max_age_seconds=3000, expose_header='ETag')
    bucket.set_cors(cors_cfg)

def create_assetstore_iam_user(bucket_name):
    import boto.iam
    iam = boto.iam.IAMConnection()
    username = bucket_name + '-user'
    iam.create_user(username)

    access_key = iam.create_access_key(username)
    result = access_key['create_access_key_response']['create_access_key_result']['access_key']
    access_key_id = result['access_key_id']
    secret_access_key = result['secret_access_key']

    policyname = username + '-s3-policy'
    policy_json = """{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": "s3:*",
          "Effect": "Allow",
          "Resource": [
            "arn:aws:s3:::%s",
            "arn:aws:s3:::%s/*"
          ]
        }
      ]
    }""" % (bucket_name, bucket_name)
    iam.put_user_policy(username, policyname, policy_json)

    return username, access_key_id, secret_access_key

def backup_assetstore_file(assetstore_file_path):
    import os
    if os.path.exists(assetstore_file_path):
        import time
        backup_path = assetstore_file_path + '.%s' % time.time()
        import shutil
        shutil.move(assetstore_file_path, backup_path)

def encrypt_assetstore_file(assetstore_file_path):
    cmd = ['ansible-vault', 'encrypt', assetstore_file_path, '--vault-password-file', 'vault-password.txt']
    import subprocess
    subprocess.call(cmd)

def create_assetstore_file(pod, username, access_key_id, secret_access_key):
    assetstore_file_path = 'pod_static_vars/%s_s3_assetstore.yml' % pod
    backup_assetstore_file(assetstore_file_path)

    pod_assetstore_vars = """---
assetstore_bucketname: %s
iam_assetstore_username: %s
iam_assetstore_access_key_id: %s
iam_assetstore_secret_access_key: %s
""" % (bucket_name, username, access_key_id, secret_access_key)

    f = open(assetstore_file_path, 'w')
    f.write(pod_assetstore_vars)
    f.close()

    encrypt_assetstore_file(assetstore_file_path)



if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print "usage:\n\npython setup_pod_s3_assetstore.py podname"

    pod = sys.argv[1]
    bucket_name = 'covalic-%s-assetstore' % pod

    bucket = get_bucket(bucket_name)
    set_bucket_policy(bucket)

    username, access_key_id, secret_access_key = create_assetstore_iam_user(bucket_name)
    create_assetstore_file(pod, username, access_key_id, secret_access_key)
