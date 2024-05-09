let loginbtn=document.getElementById("loginbtn");

      var element = document.getElementById("loginBox");
      loginbtn.addEventListener('click',()=>{
        window.scrollTo(0,700);
        element.classList.toggle("activebox");
      });


      let dismissbtn=document.getElementById("dismiss");
      dismissbtn.addEventListener('click',()=>{
        element.classList.remove("activebox");
      });

      let notifdismissbtn=document.getElementById("notifdismiss");
      notifdismissbtn.addEventListener('click',()=>{
        msgbox=document.getElementById("message");
        msgbox.classList.toggle("notactivebox");
      });


      function copyLink(elementId) {
        var linkElement = document.getElementById(elementId);
        if (linkElement) {
          var link = linkElement.getAttribute("href");
          copyToClipboard(link);
        }
      }
      
      function copyToClipboard(text) {
        navigator.clipboard
          .writeText(text)
          .then(function () {
            alert("Link copied to clipboard: " + text);
          })
          .catch(function (err) {
            console.error("Failed to copy: ", err);
          });
      }
      