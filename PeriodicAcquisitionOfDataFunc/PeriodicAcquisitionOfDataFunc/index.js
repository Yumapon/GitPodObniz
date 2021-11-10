module.exports = async function (context, myTimer) {
    var timeStamp = new Date().toISOString();
    
    if (myTimer.IsPastDue)
    {
        context.log('JavaScript is running late!');
    }
    context.log('JavaScript timer trigger function ran!', timeStamp); 

    // リクエスト先のURL(Soujiさんの湿度取得API)
    const url = 'https://hack2021goudou.azurewebsites.net/api/gethumid?code=gjHcmUhiNajYsy8f18vkEsV2JsoGo1LUWtEHz1A/yykhrob66kqA3w==';

    (async () => {
    try {
        const response = await fetch(url);
        const json = await response.json();
        console.log(json.origin);
    } catch (error) {
        console.log(error);
    }
    })();

    //Obnizからデータを取得(照度のみ10秒間分)
    const Obniz = require("obniz");
        var obniz = new Obniz("5388-5723");
    
    obniz.onconnect = async function () {
        //clientの用意
        var tempsens = obniz.wired("Keyestudio_TemperatureSensor", {signal:3, vcc:4, gnd:5});
        var pt550 = obniz.wired("PT550", {gnd:6, vcc:7, signal:8});
        //温度取得
        var temp = await tempsens.getWait();
        //照度取得
        var array = [];
        for (i = 0; i < 10; i++){
            var illuminance = await pt550.getWait();
            array.push(illuminance);
        }

    }

    //日照判定

    //お気に入り情報取得

    //メイン関数実行
};