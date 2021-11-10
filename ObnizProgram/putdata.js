const Obniz = require("obniz");

  var obniz = new Obniz("5388-5723");

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
              illuminance: illuminance,
              temp: temp
          },
          json: true
      }, function(err, req, data){
          console.log(data);
      });
    };
  };  
}

//Obniz接続解除時の処理
obniz.onclose = async function(){

};