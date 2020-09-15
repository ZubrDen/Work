$(document).ready(function (){
    $('#about-btn').click(function (event){
        alert('Вы нажали кнопку, используя JQuery!')
    });

    $("p").hover(function (){
    $(this).css('color', 'red');
},
    function (){
    $(this).css('color', 'blue')
    });

})



