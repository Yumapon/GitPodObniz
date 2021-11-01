import boto3
import os
import json
import time
from difflib import HtmlDiff

def lock(key):
    """
    Dynamodbにaws_request_idを格納します

    Parameters
    ----------
    key : String
        Lambdaを重複実行しないためのKEY(aws_request_id)を指定

    Returns
    ----------
    boolean
    """
    try:
        dynamodb.put_item(
            TableName = 'tgw-dxgw-lambdalock',
            Item = {'request-id':{'S':key},'status':{'S':'complete!'}},
            Expected = {'request-id':{'Exists':False}}
        )
        return True
    except Exception as e:
        return False

def DeleteRouteTokyo(Env, NewRTTableID):
    """
    東京リージョンでのTransitGateway向けのルートを削除します。（接続先アカウントのルートテーブルへ）

    Parameters
    ----------
    Env : String
        TransitGatewayの環境を指定。（st or prod）

    NewRTTableID : String
        操作対象のRoute Table IDを指定

    Returns
    ----------
    null    
    """
    route = accountb_ec2.delete_route(
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=NewRTTableID,
    )
    if Env == "st":
        route = accountb_ec2.delete_route(
            DestinationCidrBlock='10.82.0.0/16',
            RouteTableId=NewRTTableID
    )
    elif Env == "prod":
        route = accountb_ec2.delete_route(
            DestinationCidrBlock='10.162.0.0/16',
            RouteTableId=NewRTTableID
        )
    return

def DeleteRouteOsaka(Env, NewRTTableID):
    """
    大阪リージョンでのTransitGateway向けのルートを削除します。（接続先アカウントのルートテーブルへ）

    Parameters
    ----------
    Env : String
        TransitGatewayの環境を指定。（st or prod）

    NewRTTableID : String
        操作対象のRoute Table IDを指定

    Returns
    ----------
    null
    
    """
    route = accountb_ec2.delete_route(
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=NewRTTableID,
    )
    if Env == "st":
        route = accountb_ec2.delete_route(
            DestinationCidrBlock='10.83.0.0/16',
            RouteTableId=NewRTTableID
    )
    elif Env == "prod":
        route = accountb_ec2.delete_route(
            DestinationCidrBlock='10.163.0.0/16',
            RouteTableId=NewRTTableID
        )
    return

def lambda_handler(event, context):
    """
    AWS共通基盤のTransit Gatewayと別アカウントのVPCを接続削除します

    Parameters
    ----------
    event : object
        AWS Lambda はこのパラメーターを使用してイベントデータをハンドラーに渡します
    context : object
        AWS Lambda はこのパラメーターを使用して、実行中の Lambda 関数のランタイム情報をハンドラーに提供します。

    Returns
    ----------
    body: String
        Success!   
    """

    #変数宣言：クライアント
    global s3
    global ram
    global sts
    global dynamodb
    global ec2
    global accountb
    global accountb_ec2
    global accountb_ram

    # 関数Strat時の情報
    print('#####TGWConnect_Create関数を実行します')
    print('#####ENVIRONMENT VARIABLES')
    print(os.environ)
    print('#####EVENT')
    print(event)

    #[AWS共通基盤 Account] クライアント
    s3 = boto3.client('s3')
    ram = boto3.client('ram')
    sts = boto3.client('sts')
    dynamodb = boto3.client('dynamodb')
    ec2 = boto3.client('ec2')

    #Lambda実行のIDを取得
    aws_request_id = context.aws_request_id

    # 冪等性担保のためのロック確認処理
    if(lock(aws_request_id)):
        print('#####呼び出しが重複されないよう、ロックします')
    else:
        print('#####すでに同じリクエストでLambdaが実行されているようです')
        return { "body" : json.dumps('##### すでに同じリクエストでLambdaが実行されているようです')}

    # Event情報を取得し、設定ファイルをPUTされたS3の情報を取得する
    BUCKET_NAME = event['Records'][0]['s3']['bucket']['name']
    OBJECT_KEY = event['Records'][0]['s3']['object']['key'] 

    # S3に格納された設定ファイルを取得
    # クライアントを使用してS3からレスポンスを取得後、整形する
    print('#####S3から設定ファイルを取得します')

    object = s3.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
    body = object['Body'].read()
    inputConfigFile = json.loads(body.decode('utf-8'))

    # 設定ファイルや環境変数から設定値を取得
    print('#####設定値を取得しています')

    #環境変数から取得
    Env = os.environ['ENV']
    AWSCommonAccountID = os.environ['AWSCOMMONACCOUNRID']
    TransitGatewayID = os.environ['TRANSITGATEWAYID']
    SPKRouteTableID = os.environ['SPKROUTETABLEID']
    SECRouteTableID = os.environ['SECROUTETABLEID']

    #設定ファイルから取得
    ProcessType = inputConfigFile['ProcessType']
    ResionName = inputConfigFile['ResionName']
    RAMName = inputConfigFile['RAMName']
    TGWAttachNameTag = inputConfigFile['TGWAttachNameTag']
    NewAWSAccID = inputConfigFile['NewAWSAccID']
    NewRoleArn = inputConfigFile['NewRoleArn']
    NewTGWAttachVPCName = inputConfigFile['NewTGWAttachVPCName']
    NewTGWAttachVPCCidr = inputConfigFile['NewTGWAttachVPCCidr']
    NewTGWAttachSubnets = inputConfigFile['NewTGWAttachSubnets']
    NewRouteTables = inputConfigFile['NewRouteTables']
    EditRoute = inputConfigFile['EditRoute']

    #接続先アカウントへのSTS Connection
    accountb = sts.assume_role(
        RoleArn = NewRoleArn,
        RoleSessionName="cross_acct_lambda"
    )
    ACCESS_KEY = accountb['Credentials']['AccessKeyId']
    SECRET_KEY = accountb['Credentials']['SecretAccessKey']
    SESSION_TOKEN = accountb['Credentials']['SessionToken']

    #接続先アカウントへのSTS Connection
    accountb_ec2 = boto3.client(
        'ec2',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN,
        region_name=ResionName
    )

    accountb_ram = boto3.client(
        'ram',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN,
        region_name=ResionName
    )

    # Processタイプのチェック
    print('#####プロセスタイプを判定しています。')
    if ProcessType != "TGWDelete":
        return { "body" : json.dumps('##### Process correspondence is different')}
    print('#####プロセスタイプの確認ができました')

    ############################################################################
    # 設定ファイルで指定したVPC等の新規接続先アカウントのリソース有無をチェック
    ############################################################################

    #---VPCのチェック
    #設定ファイルに記載した新規アカウント側のVPC名と同じNameTagのVPCが２つ以上あるか、１つもない場合処理を終了。
    #1つ存在する場合のみ処理を継続
    response_describe_vpcs = accountb_ec2.describe_vpcs(
    Filters=[
        {
            "Name": "tag:Name",
            "Values": [
                NewTGWAttachVPCName,
            ]
        },
    ]
    )
    if (len(response_describe_vpcs['Vpcs']) > 1):
        print('VPC ' + NewTGWAttachVPCName + 'が' + str(len(response_describe_vpcs['Vpcs'])) + ' 個存在します。処理を終了します')
        return { 'body' : json.dumps('##### There is multiple VPCs')}
    elif (len(response_describe_vpcs['Vpcs']) == 0):
        print('VPC ' + NewTGWAttachVPCName + ' がありません')
        return { 'body' : json.dumps('##### NO VPC')}
    else:
        print('新規アカウント側に指定されたVPCが存在します。処理を継続します')
        VPCID = response_describe_vpcs['Vpcs'][0]['VpcId']

    #---アタッチメントのチェック
    response = accountb_ec2.describe_transit_gateway_attachments(
        Filters=[
            {
                "Name": "tag:Name",
                "Values": [
                    TGWAttachNameTag,
                ]
            },
            {
                "Name": "resource-id",
                'Values': [
                    VPCID,
                ]
            },
            {
                "Name": "state",
                'Values': [
                    "available",
                ]
            },
        ]
    )
    if (len(response['TransitGatewayAttachments']) == 0):
        print('TGWAttachment ' + NewTGWAttachVPCName + ' がありません')
        return { 'body' : json.dumps('##### NO TGWAttachment')}
    else:
        print('TGWAttachmentが存在します。処理を継続します')
        TGWAttachmentId = response['TransitGatewayAttachments'][0]['TransitGatewayAttachmentId']

    #---RAMのチェック
    response = ram.get_resource_shares(
        resourceShareStatus='ACTIVE',
        resourceOwner='SELF',
        name=RAMName
    )
    if (len(response['resourceShares']) == 0):
        print('RAM ' + RAMName + ' がありません')
        return { 'body' : json.dumps('##### NO RAM')}
    else:
        print('RAMが存在します。処理を継続します')
        ResourceShareArn = response['resourceShares'][0]['resourceShareArn']    

    # Transit Gatewayの現状設定値を確認
    print('#####作業前のTGW設定値を取得します')
    #SPKの設定値
    before_spk_associations = ec2.get_transit_gateway_route_table_associations(
         TransitGatewayRouteTableId = SPKRouteTableID
    )
    #SECの設定値
    before_sec_routes = ec2.search_transit_gateway_routes(
        TransitGatewayRouteTableId = SECRouteTableID,
        Filters = [
            {
                'Name': 'state',
                'Values': [
                    'active',
                    'blackhole'
                ],
            }
        ]
    )

    #######################################
    # ここからリソースの削除等環境への変更を実施 #
    #######################################
    print('#####ここからリソースの削除や変更の処理が流れます')

    print('#####TGWのSECルートテーブルからルートを削除します')
    response = ec2.delete_transit_gateway_route(
        TransitGatewayRouteTableId=SECRouteTableID,
        DestinationCidrBlock=NewTGWAttachVPCCidr,
    )
    print('#####TGWのSECルートテーブルからルートを削除しました')

    print('#####TGWのSPKルートテーブルからアタッチメントの関連づけを削除します')
    response = ec2.disassociate_transit_gateway_route_table(
        TransitGatewayRouteTableId=SPKRouteTableID,
        TransitGatewayAttachmentId=TGWAttachmentId
    )
    print('#####TGWのSPKルートテーブルからアタッチメントの関連づけを削除しました')

    print('#####TGWのアタッチメントを削除します')
    response = accountb_ec2.delete_transit_gateway_vpc_attachment(
        TransitGatewayAttachmentId=TGWAttachmentId,
    )
    print('#####TGWのアタッチメントを削除しました')

    print('#####RAMを削除します')
    response = ram.delete_resource_share(
        resourceShareArn=ResourceShareArn
    )
    print('#####RAMを削除しました')

    # ルートテーブルの編集
    if (EditRoute == "yes"):

        print('#####VPCのルートテーブルを編集します')
        for item in NewRouteTables.values():
            #編集するRouteTableのIDを取得
            response = accountb_ec2.describe_route_tables(
                Filters=[
                    {
                        'Name': "tag:Name",
                        'Values': [
                            item["Name"],
                        ]
                    },
                ],
            )
            NewRTTableID = response['RouteTables'][0]['RouteTableId']

            #####RouteTableへのRoute追加
            if ResionName == "ap-northeast-1":
                DeleteRouteTokyo(Env, NewRTTableID)
            elif ResionName == "ap-northeast-3":
                DeleteRouteOsaka(Env, NewRTTableID)
            print('RouteTable名' + item["Name"] + 'を編集しました')

        print('#####VPCのルートテーブルの編集が完了しました')

    ##########################
    # 作業前後のデグレ確認
    ##########################
    # Transit Gatewayの作業後設定値を確認
    time.sleep(30)
    print('#####作業後のTGW設定値を取得します')
    #SPKの設定値
    after_spk_associations = ec2.get_transit_gateway_route_table_associations(
         TransitGatewayRouteTableId = SPKRouteTableID
    )
    #SECの設定値
    after_sec_routes = ec2.search_transit_gateway_routes(
        TransitGatewayRouteTableId = SECRouteTableID,
        Filters = [
            {
                'Name': 'state',
                'Values': [
                    'active',
                    'blackhole'
                ],
            }
        ]
    )

    # Transit GatewayのDiff確認
    print('#####作業後のデグレ確認を実施しています')
    # 書き込み先ファイルを作成。設定前
    fp_spk_before = open('/tmp/fp_spk_before.json', 'w')
    fp_sec_before = open('/tmp/fp_sec_before.json', 'w')
    # ファイルの書き込み
    json.dump(before_spk_associations, fp_spk_before, indent=4)
    json.dump(before_sec_routes, fp_sec_before, indent=4)
    fp_spk_before.close()
    fp_sec_before.close()

    # 書き込み先ファイルを作成。設定後
    fp_spk_after = open('/tmp/fp_spk_after.json', 'w')
    fp_sec_after = open('/tmp/fp_sec_after.json', 'w')
    #ファイルの書き込み
    json.dump(after_spk_associations, fp_spk_after, indent=4)
    json.dump(after_sec_routes, fp_sec_after, indent=4)
    fp_spk_after.close()
    fp_sec_after.close()

    with open('/tmp/fp_spk_before.json', 'r') as f:
        file1 = f.readlines()
    with open('/tmp/fp_spk_after.json', 'r') as f:
        file2 = f.readlines()
    with open('/tmp/fp_sec_before.json', 'r') as f:
        file3 = f.readlines()
    with open('/tmp/fp_sec_after.json', 'r') as f:
        file4 = f.readlines()

    df = HtmlDiff()
    with open('/tmp/spk_diff.html', 'w') as html:
        html.writelines(df.make_file(file2, file1))
    with open('/tmp/sec_diff.html', 'w') as html:
        html.writelines(df.make_file(file4, file3))

    s3obj = boto3.resource('s3')
    s3obj.meta.client.upload_file('/tmp/spk_diff.html', 'lambdakickbucket', 'spk_diff.html')
    s3obj.meta.client.upload_file('/tmp/sec_diff.html', 'lambdakickbucket', 'sec_diff.html')

    os.remove('/tmp/fp_spk_before.json')
    os.remove('/tmp/fp_spk_after.json')
    os.remove('/tmp/fp_sec_before.json')
    os.remove('/tmp/fp_sec_after.json')

    print('#####デグレ確認はS3へ格納しました')

    return {'body': json.dumps('Success!')}