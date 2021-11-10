module.exports = async function (context, myTimer) {
    var timeStamp = new Date().toISOString();
    
    if (myTimer.IsPastDue)
    {
        context.log('JavaScript is running late!');
    }
    context.log('JavaScript timer trigger function ran!', timeStamp); 

    const Obniz = require("obniz");
        var obniz = new Obniz("5388-5723");

    obniz.onconnect = async function () {
    //clientの用意
    var tempsens = obniz.wired("Keyestudio_TemperatureSensor", {signal:3, vcc:4, gnd:5});
    var pt550 = obniz.wired("PT550", {gnd:6, vcc:7, signal:8});
    //温度取得
    var temp = await tempsens.getWait();
    console.log("温度:" + temp)
    //照度取得
    var array = [];
    for (i = 0; i < 10; i++){
        var illuminance = await pt550.getWait();
        array.push(illuminance);
        console.log("照度:" + illuminance)
    }
    //照度の平均
    let averageill = 0;

    array.forEach(function(v) {
        averageill += v;
    });

    averageill = averageill / array.length
    console.log("平均照度:" + averageill);

    //日照判定
    var sun = false;
    if (averageill > 4.5){sun = true;};
    console.log(sun);

    //お気に入り情報をcosmosdbから取得

    //メイン関数実行
    }
};