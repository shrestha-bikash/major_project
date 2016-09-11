if ( XMLHttpRequest.prototype.sendAsBinary === undefined ) {
    XMLHttpRequest.prototype.sendAsBinary = function(string) {
        var bytes = Array.prototype.map.call(string, function(c) {
            return c.charCodeAt(0) & 0xff;
        });
        this.send(new Uint8Array(bytes).buffer);
    };
};

(function(d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) return;
  js = d.createElement(s); js.id = id;
  js.src = "//connect.facebook.net/en_US/all.js";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));

window.fbAsyncInit = function() {
    FB.init({
      appId  : "1309139539100169",
      status : true,
      cookie : true,
      xfbml  : true  // parse XFBML
    });
};

function postImageToFacebook( authToken, filename, mimeType, imageData, message )
{
    // this is the multipart/form-data boundary we'll use
    var boundary = '----personalitypredictionboundary';
    // let's encode our image file, which is contained in the var
    var formData = '--' + boundary + '\r\n'
    formData += 'Content-Disposition: form-data; name="source"; filename="' + filename + '"\r\n';
    formData += 'Content-Type: ' + mimeType + '\r\n\r\n';
    for ( var i = 0; i < imageData.length; ++i )
    {
        formData += String.fromCharCode( imageData[ i ] & 0xff );
    }
    formData += '\r\n';
    formData += '--' + boundary + '\r\n';
    formData += 'Content-Disposition: form-data; name="message"\r\n\r\n';
    formData += message + '\r\n'
    formData += '--' + boundary + '--\r\n';

    var xhr = new XMLHttpRequest();
    xhr.open( 'POST', 'https://graph.facebook.com/me/photos?access_token=' + authToken, true );
    xhr.onload = xhr.onerror = function() {
        console.log( xhr.responseText );
    };
    xhr.setRequestHeader( "Content-Type", "multipart/form-data; boundary=" + boundary );
    xhr.sendAsBinary( formData );
};


var authToken;
var msg;
function postCanvasToFacebook() {
  msg = document.getElementById("getText").value;

  html2canvas($("#score"),{
    onrendered: function(canvas){

      // getting the div canvas as a URL
      var data = canvas.toDataURL("image/png");
    	var encodedPng = data.substring(data.indexOf(',') + 1, data.length);
    	var decodedPng = Base64Binary.decode(encodedPng);
    	FB.getLoginStatus(function(response) {
    	  if (response.status === "connected") {
    		    postImageToFacebook(response.authResponse.accessToken, "result", "image/png", decodedPng, msg);
    	  }
    	 });

    }

  });
  myvar = setTimeout(postCloudToFacebook, 1000);

};

function postCloudToFacebook(){
  var html = d3.select("svg")
        .attr("version", 1.1)
        .attr("xmlns", "http://www.w3.org/2000/svg")
        .node().parentNode.innerHTML;
  var imgsrc = 'data:image/svg+xml;base64,'+ btoa(html);

  var canvas = document.querySelector("canvas"),
	context = canvas.getContext("2d");

  var image = new Image;
  image.src = imgsrc;
  image.onload = function(){
    context.drawImage(image, 0, 0);
    var data = canvas.toDataURL("image/png");
  	var encodedPng = data.substring(data.indexOf(',') + 1, data.length);
  	var decodedPng1 = Base64Binary.decode(encodedPng);
  	FB.getLoginStatus(function(response) {
  	  if (response.status === "connected") {
  		    postImageToFacebook(response.authResponse.accessToken, "result", "image/png", decodedPng1, msg);
  	  }
  	 });
  };


  // html2canvas($(".wcloud"),{
  //   onrendered: function(canvas){
  //     // getting the div canvas as a URL
  //

  //   }
  //
  // });
};
