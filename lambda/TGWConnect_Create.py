import boto3
import os
import json
import time
from difflib import HtmlDiff
#TODO AWS共通基盤側のアタッチメントに名前をつける

#TODO: 要修正(冪等性判断はaws_request_idで良いのか)
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

def AddRouteTokyo(Env, TransitGatewayID, NewRTTableID):
    """
    東京リージョンでのTransitGateway向けのルートを追加します。（接続先アカウントのルートテーブルへ）

    Parameters
    ----------
    Env : String
        TransitGatewayの環境を指定。（st or prod）

    TransitGatewayID : String
        TransitGatewayのIDを指定

    NewRTTableID : String
        操作対象のRoute Table IDを指定

    Returns
    ----------
    null    
    """
    #0.0.0.0/0をTransitGatewayに向ける
    print('0.0.0.0/0のルートを追加します')
    route = accountb_ec2.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        TransitGatewayId=TransitGatewayID,
        RouteTableId=NewRTTableID
    )
    print('0.0.0.0/0のルートを追加しました')
    #東京リージョンSTは10.82.0.0/16でAWSが切られているので、TGWに向けとく
    if Env == "st":
        print('10.82.0.0/16のルートを追加します')
        route = accountb_ec2.create_route(
            DestinationCidrBlock='10.82.0.0/16',
            TransitGatewayId=TransitGatewayID,
            RouteTableId=NewRTTableID
        )
        print('10.82.0.0/16のルートを追加しました')
    #東京リージョンProdは10.162.0.0/16でAWSが切られているので、TGWに向けとく
    elif Env == "prod":
        print('10.162.0.0/16のルートを追加します')
        route = accountb_ec2.create_route(
            DestinationCidrBlock='10.162.0.0/16',
            TransitGatewayId=TransitGatewayID,
            RouteTableId=NewRTTableID
        )
        print('10.162.0.0/16のルートを追加しました')
    return

def AddRouteOsaka(Env, TransitGatewayID, NewRTTableID):
    """
    大阪リージョンでのTransitGateway向けのルートを追加します。（接続先アカウントのルートテーブルへ）

    Parameters
    ----------
    Env : String
        TransitGatewayの環境を指定。（st or prod）

    TransitGatewayID : String
        TransitGatewayのIDを指定

    NewRTTableID : String
        操作対象のRoute Table IDを指定

    Returns
    ----------
    null
    
    """
    #デフォゲをTransitGatewayに向ける
    print('0.0.0.0/0のルートを追加します')
    route = accountb_ec2.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        TransitGatewayId=TransitGatewayID,
        RouteTableId=NewRTTableID
    )
    print('0.0.0.0/0のルートを追加しました')
    #大阪リージョンSTは10.83.0.0/16でAWSが切られているので、TGWに向けとく
    if Env == "st":
        print('10.83.0.0/16のルートを追加します')
        route = accountb_ec2.create_route(
            DestinationCidrBlock='10.83.0.0/16',
            TransitGatewayId=TransitGatewayID,
            RouteTableId=NewRTTableID
        )
        print('10.83.0.0/16のルートを追加しました')
    #大阪リージョンProdは10.163.0.0/16でAWSが切られているので、TGWに向けとく
    elif Env == "prod":
        print('10.163.0.0/16のルートを追加します')
        route = accountb_ec2.create_route(
            DestinationCidrBlock='10.163.0.0/16',
            TransitGatewayId=TransitGatewayID,
            RouteTableId=NewRTTableID
        )
        print('10.163.0.0/16のルートを追加しました')
    return

def lambda_handler(event, context):
    """
    AWS共通基盤のTransit Gatewayと、別アカウントのVPCを接続します

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
    global accountb_ec2
    global accountb_ram
    global s3obj

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

    #TGWのARNを取得
    transitinfo = ec2.describe_transit_gateways(
        TransitGatewayIds=[
            TransitGatewayID,
        ]
    )
    TGWArn = transitinfo['TransitGateways'][0]['TransitGatewayArn']

    #接続先アカウントへのSTS Connection
    accountb = sts.assume_role(
        RoleArn = NewRoleArn,
        RoleSessionName="cross_acct_lambda"
    )
    ACCESS_KEY = accountb['Credentials']['AccessKeyId']
    SECRET_KEY = accountb['Credentials']['SecretAccessKey']
    SESSION_TOKEN = accountb['Credentials']['SessionToken']

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
    if ProcessType != "TGWCreate":
        return { "body" : json.dumps('##### Process correspondence is different')}
    print('#####プロセスタイプの確認ができました')

    # RAMがすでに存在していないか確認
    print('#####RAMがすでに作成されていないか確認中です(ASSOCIATED)')
    responce = ram.get_resource_share_associations(
        associationType='PRINCIPAL',
        associationStatus='ASSOCIATED'
    )
    for id in responce['resourceShareAssociations']:
        if id['associatedEntity'] == NewAWSAccID:
            print('#####すでにRAMが共有されているようです')
            return { "body" : json.dumps('#####already connectioned')}
    print('#####RAMがすでに作成されていないか確認中です(ASSOCIATING)')
    responce = ram.get_resource_share_associations(
        associationType='PRINCIPAL',
        associationStatus='ASSOCIATING'
    )
    for id in responce['resourceShareAssociations']:
        if id['associatedEntity'] == NewAWSAccID:
            print('#####すでにRAMの共有が実施中です')
            return { "body" : json.dumps('#####already connecting')}

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

    #---Subnetのチェック
    NewSubnetIDs = []
    for item in NewTGWAttachSubnets.values():
        response_describe_subnets = accountb_ec2.describe_subnets(
            Filters=[
                {
                    "Name": "tag:Name",
                    "Values": [
                        item["Name"]
                    ]
                },
            ]
        )
        if (len(response_describe_subnets['Subnets']) > 1):
            print('Subnet ' + item + 'が' + str(len(response_describe_vpcs['Subnets'])) + ' 個存在します。処理を終了します')
            return { 'body' : json.dumps('##### There is multiple Subnets')}
        elif (len(response_describe_subnets['Subnets']) == 0):
            print('Subnet ' + item + ' がありません')
            return { 'body' : json.dumps('##### NO Subnet')}
        else:
            subnetid = response_describe_subnets['Subnets'][0]['SubnetId']
            NewSubnetIDs.append(subnetid)

    #---RouteTableのチェック
    #TODO:

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
                'Name': 'attachment.resource-type',
                'Values': [
                    'vpc',
                    'vpn',
                    'direct-connect-gateway',
                    'peering',
                    'connect'
                ],
            }
        ]
    )

    #######################################
    # ここからリソースの作成等環境への変更を実施 #
    #######################################
    print('#####ここからリソースの作成や変更の処理が流れます')

    # RAMを使用したTGWの招待
    print('#####リソース共有を実施します')
    response_create_resource_share = ram.create_resource_share(
        name=RAMName,
        resourceArns=[
            TGWArn,
        ],
        principals=[
            NewAWSAccID,
        ],
        tags=[
            {
                "key": "Name",
                "value": RAMName
            }
        ],
        allowExternalPrincipals=True
    )
    print("#####リソース共有を提案しました。20秒待機した後、承諾します")
    time.sleep(20)

    # RAMの承諾
    print('#####リソースの共有を承諾します')
    #リソース共有招待のArnを取得
    responce_invite = accountb_ram.get_resource_share_invitations(
        resourceShareArns=[
                response_create_resource_share['resourceShare']['resourceShareArn'],
        ]    
    )
    #リソース共有を承諾
    response_accept_resource_share = accountb_ram.accept_resource_share_invitation(
        resourceShareInvitationArn=responce_invite['resourceShareInvitations'][0]['resourceShareInvitationArn'],
    )
    print('#####リソースの共有を承諾しました') 

    # TGWアタッチメントの作成
    print('#####TGWアタッチメントを作成します')
    #これ入れないと、アタッチメントが認識できない。。内部処理が間に合ってない？
    time.sleep(20)

    #アタッチメントを作成
    #VPCIDやSubnet IDはリソースの有無確認フェーズにて取得済みのものを使用
    response_create_tgw_vpc_attachment = accountb_ec2.create_transit_gateway_vpc_attachment(
        TransitGatewayId=TransitGatewayID,
        VpcId=VPCID,
        SubnetIds=NewSubnetIDs,
        Options={
            'DnsSupport': 'enable',
            'Ipv6Support': 'disable'
        },
        TagSpecifications=[
            {
                'ResourceType': 'transit-gateway-attachment',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': TGWAttachNameTag
                    },
                ]
            },
        ]
    )

    print('#####TGWアタッチメントを作成しました')

    print('#####TGWAttachmentがアップするのを待ちます')
    TGWAttachmentId=response_create_tgw_vpc_attachment['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
    #現在のアタッチメントの状態確認
    #availableになるまでwhile文で確認し続ける
    response = accountb_ec2.describe_transit_gateway_vpc_attachments(
        TransitGatewayAttachmentIds=[
            TGWAttachmentId,
        ],
        Filters=[
            {
                'Name': "transit-gateway-id",
                'Values': [
                    TransitGatewayID,
                ]
            },
        ]
    )
    state = "available"
    state_now = response['TransitGatewayVpcAttachments'][0]['State']
    while state != state_now:
        print("#####Now Loading.....TGW & VPC Attachment State = " + state_now) 
        time.sleep(1)
        response = accountb_ec2.describe_transit_gateway_vpc_attachments(
            TransitGatewayAttachmentIds=[
                TGWAttachmentId,
            ],
            Filters=[
                {
                    'Name': "transit-gateway-id",
                    'Values': [
                        TransitGatewayID,
                    ]
                },
            ]
        )
        state_now = response['TransitGatewayVpcAttachments'][0]['State']
    print("#####Status OK!!!.....TGW & VPC Attachment State = " + state_now)

    # TGWのルートテーブルを編集
    print('#####TGWのルートテーブルを編集します')
    #まずはSPK RouteTable
    response = ec2.associate_transit_gateway_route_table(
        TransitGatewayRouteTableId=SPKRouteTableID,
        TransitGatewayAttachmentId=TGWAttachmentId
    )
    #次はSPK RouteTable
    response = ec2.create_transit_gateway_route(
        DestinationCidrBlock=NewTGWAttachVPCCidr,
        TransitGatewayRouteTableId=SECRouteTableID,
        TransitGatewayAttachmentId=TGWAttachmentId
    )
    print('#####TGWのルートテーブルの編集が完了しました')

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
                AddRouteTokyo(Env, TransitGatewayID, NewRTTableID)
            elif ResionName == "ap-northeast-3":
                AddRouteOsaka(Env, TransitGatewayID, NewRTTableID)
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
                'Name': 'attachment.resource-type',
                'Values': [
                    'vpc',
                    'vpn',
                    'direct-connect-gateway',
                    'peering',
                    'connect'
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