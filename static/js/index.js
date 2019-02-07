
$(function() {

    let width = 28
    let height = 28
    let batch = 200
    let noise = 30

    function inverse(array) {
        return array.map(i => { return 1.0 - i })
    }

    $.getJSON("/_mnist/" + batch + "/" + noise, function(resp) {
        let $canvasBag = $('#canvas-bag')
        resp.data.forEach((digit) => {
            let $canvas = $('<canvas>')
                .attr('width', width)
                .attr('height', height)
            $canvasBag.append($canvas)
            mnist.draw(inverse(digit.flat(2)), $canvas[0].getContext('2d'))
        })
    });
})
