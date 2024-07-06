odoo.define('ki_car_services.cars', function (require) {
'use strict';

var rpc = require('web.rpc');
var weContext = require('web_editor.context');
require('web.dom_ready');

$('.brand_id').on('change', function(){
    var brand_id = $('.brand_id').find(":selected").attr('value');
    $(".car[brand!="+brand_id+"]").css('display','none');
    $(".car[brand="+brand_id+"]").css('display','block');
});
$('.brand_id').trigger('change');

$('.slot').on('click', function(){
    var slot = $(this).attr('name');
    $("input[name=slot_select]").val(slot);
    var hrs = parseInt(Number(slot));
    $("strong#selected_slot").text((hrs < 10 ? "0" : "") + (hrs) + ':00');
});


});
