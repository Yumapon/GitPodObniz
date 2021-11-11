const Obniz = require("obniz");
var obniz = new Obniz("5388-5723");

const request = require('request');

//Obniz接続時の処理
obniz.onconnect = async function () {

  //clientの用意
  var button = obniz.wired("Keyestudio_Button", {signal:0, vcc:1, gnd:2});
  var tempsens = obniz.wired("Keyestudio_TemperatureSensor", {signal:3, vcc:4, gnd:5});
  var pt550 = obniz.wired("PT550", {gnd:6, vcc:7, signal:8});

  //ボタン押下時にAzure Functionを呼び出す 
  button.onchange = async function(pressed){
    console.log("pressed:" + pressed)

    //ボタン押下時のみ実行
    if(!pressed){
      //情報を取得
      var illuminance = await pt550.getWait();
      var temp = await tempsens.getWait();

      console.log(illuminance)
      console.log(temp)

      //API呼び出し
      const request = require('request');
      var URL = 'https://getinputdatafunc.azurewebsites.net/api/getinputdata';
      request.get({
          url: URL,
          headers: {'Content-type': 'application/json'},
          qs: {
              "illuminance": illuminance,
              "temp": temp,
              "code": "GNwUmfVwJB6hBoaoh4a9lKi8zHVofrW2F69nXCF/Ci1vfNS8Nc1X9w=="
          },
          json: true
      }, function(err, req, data){
          console.log(data);
      });
    };
  };
  
  obniz.repeat(async () => {
    console.log("定期実行")
    
    //温度取得
    var temp = await tempsens.getWait();
    console.log("温度:" + temp)
    //照度取得
    var array = [];
    for (i = 0; i < 10; i++){
        var illuminance = await pt550.getWait();
        array.push(illuminance);
        console.log("照度:" + illuminance);
        await obniz.wait(1000);
    }
    //照度の平均
    let averageill = 0;

    array.forEach(function(v) {
      averageill += v;
    });

    averageill = averageill / array.length
    console.log("平均照度:" + averageill);

    //照度の平均と温度を送信
    //API呼び出し      
    var URL = 'https://periodicacquisitionofdatafunc2.azurewebsites.net/api/periodicacquisitionofdatafunc';
      request.get({
        url: URL,
        headers: {'Content-type': 'application/json'},
        qs: {
            "averageill": averageill,
            "temp": temp
        },
        json: true
    }, function(err, req, data){
        console.log(data);
    });
  },300000 );
}

//Obniz接続解除時の処理
obniz.onclose = async function(){

}
