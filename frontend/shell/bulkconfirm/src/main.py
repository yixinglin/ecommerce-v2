from piplines import AmazonBulkConfirmPipeline

if __name__ == '__main__':
    HOST = 'http://192.168.8.140:5018'
    AmazonBulkConfirmPipeline(HOST).process()