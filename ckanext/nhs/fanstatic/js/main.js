// Main Javascript file for  ed portal

//Adding scrollspy to the pages like about
$('body').scrollspy({ target: '#spy', offset:280});

//Calculate the position of scroll for
$(window).on('load',function(){
    calcScrollLocation();
});

$(window).scroll(function() {    
    calcScrollLocation();
}); 

function calcSidebarHeight(){
    var height = $(".module-content").outerHeight();
    $(".sidebar").height(height);
};

function calcScrollLocation(){
    var scroll = $(window).scrollTop();
}

$('a.feedback_mail').on('click', function(){
    window.location.href = "mailto:odpfeedback@ed.gov";
});

$(document).ready(function(){

    //Checks the page name via page tag
    var page = $('body').find('.page-home').text();

    /* Particles js for homepage */
    if(page=="home"){
        renderParticles();
    }


    //Showing scrollbar on specific page for devices larger than 768px
    if(page=="search" || page=="publisher_listing"){
        if ($(window).width() >= 768) {
            new SimpleBar($('#scrollbar')[0]);
        }

        $("p.module-content.empty").attr("tabindex","0");
    }

    if(page=="dataset"){
        //Changing navicons programatiically 
        $(".view_list").html("view_list");
        $(".info").html("info");
        $(".add_comment").html("add_comment");
        $(".bar_chart").html("bar_chart");
        $(".supervisor_account").html("supervisor_account");
    }


    //Subpage 
    var subpage = $('body').find('.page-name-sub').text();

    if(subpage=="data"){
        $(".nav-tabs > li:first-child").addClass("active");
    }

    var navHeight = $("#nav-wrapper").outerHeight();
    $("body").css("paddingTop",navHeight);
}); 

//Using Particles.js for homepage
function renderParticles(){
    particlesJS("hero", {
        "particles": {
            "number": {
                "value":20, "density": {
                    "enable": true, "value_area": 1000
                }
            }
            , "color": {
                "value": ["#3da650", "#0372e4"]
            }
            , "shape": {
                "type":"edge", "stroke": {
                    "width": 0, "color": "#000000"
                }
                , "polygon": {
                    "nb_sides": 10
                }
                , "image": {
                    "src": "img/github.svg", "width": 100, "height": 100
                }
            }
            , "opacity": {
                "value":1, "random":false, "anim": {
                    "enable": false, "speed": 1, "opacity_min": 0, "sync": false
                }
            }
            , "size": {
                "value":5.5, "random":true, "anim": {
                    "enable": false, "speed": 4, "size_min": 3.5, "sync": false
                }
            }
            , "line_linked": {
                "enable": false, "distance": 150, "color": "#ffffff", "opacity": 0.4, "width": 1
            }
            , "move": {
                "enable":true, "speed":1, "direction":"none", "random":true, "straight":false, "out_mode":"out", "bounce":false, "attract": {
                    "enable": false, "rotateX": 600, "rotateY": 600
                }
            }
        }
        , "interactivity": {
            "detect_on":"canvas", "events": {
                "onhover": {
                    "enable": false, "mode": "bubble"
                }
                , "onclick": {
                    "enable": false, "mode": "repulse"
                }
                , "resize":true
            }
            , "modes": {
                "grab": {
                    "distance":400, "line_linked": {
                        "opacity": 1
                    }
                }
                , "bubble": {
                    "distance": 85.26810729164123, "size": 0, "duration": 2, "opacity": 0, "speed": 3
                }
                , "repulse": {
                    "distance": 400, "duration": 0.4
                }
                , "push": {
                    "particles_nb": 4
                }
                , "remove": {
                    "particles_nb": 2
                }
            }
        }
        , "retina_detect":true
    });

    //Calculating the canvas height to ensure particles take up full space
    function calcCanvasHeight(){
        setTimeout(function() { 
            $(".hero > canvas").height("400px");
            $(".hero > canvas").attr("height",400);
         },1);
    }
    

}