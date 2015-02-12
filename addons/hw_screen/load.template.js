var template;
var Qweb = openerp.qweb;

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

var loadTemplate = function() {
    setInterval(function(){
        $.ajax({ url: "server", success: function(r){
            if(!!r.template) {
                Qweb.add_template(r.template);
            }
            if(!!r.data && !!r.name) {
                template = $(Qweb.render(r.name, r.data));
                switchSlide($('body').children(),template);
            }
        }, dataType: "json"});
    }, 30000);
};
