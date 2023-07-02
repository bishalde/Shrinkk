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