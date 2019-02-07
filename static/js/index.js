
$(function() {

    let width = 28
    let height = 28

    $.getJSON( "/_mnist/200/0", function(resp) {
        let $canvasBag = $('#canvas-bag')
        resp.data.forEach((digit) => {
            let $canvas = $('<canvas>')
                .attr('width', width)
                .attr('height', height)
            $canvasBag.append($canvas)
            mnist.draw(digit.flat(2), $canvas[0].getContext('2d'))
        })
    });
})
