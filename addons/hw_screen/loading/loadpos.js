var data = null;
var posScreen = null;
var loading;
var extend;
var wait;
var update;

$.fn.appendSlide = function(delay, callback) {
    var self = this;

    this.promise().done(function() {
        var z_index = this.css('z-index');
        self.hide()
            .css('z-index',9999)
            .appendTo('body')
            .fadeIn(delay, callback);
        setTimeout(function() {
            self.css('z-index',z_index);
        },3*delay);
    });
    return this;
};

$.fn.removeSlide = function(delay, callback) {
    var self = this;
    this.promise().done(function() {
        self.fadeOut(delay, function() {
                callback.apply(this);
                this.remove();
            });
    });
    return this;
};

var switchSlide = function (oTemplate, nTemplate) {
    nTemplate.appendSlide(1000);
    oTemplate.removeSlide(1000);
};

extend = function (Data, Obj) {
    $.each(Obj, function (Value, Label) {
        if ((typeof Data[Label] === 'object') &&
            (typeof Value       === 'object')) {

            if (Data[Label] && Value) {
                extend(Data[Label], Value);
            }
            else {
                Data[Label] = Value;
            }
        }
        else {
            Data[Label] = Value;
        }
    });
};

wait = function () {
    setTimeout(loading, 1000);
};

update = function (newData) {
    if (!newData) {
        wait();
    }
    extend(data, newData);
    if (newData.url != data.url) {
        data.url = newData.url;
        var NewPosScreen = $('<iframe src="'+url+'"></iframe>');
        switchSlide(posScreen, NewPosScreen);
        posScreen = NewPosScreen;
        wait();
    }
};

loading = function () {
    $.get('http://localhost:8069/screen/get_data', update).error(wait);
};

posScreen = $('<iframe src=""></iframe>');
posScreen.appendTo('body');

$(window).load(loading);
