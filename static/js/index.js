
$(function() {

    // DOM stuff used below
    let $canvasBag = $('#canvas-bag')
    let $noiseSlider = $('#noise')
    let $noiseLabel = $('#noise-label')
    let $spinner = $('.spinner-border')

    // Functions

    function inverse(array) {
        return array.map(i => { return 1.0 - i })
    }

    function getMnist(batch, noise, cb) {
      $.getJSON("/_mnist/" + batch + "/" + noise, cb);
    }

    /* From http://stackoverflow.com/questions/7128675/from-green-to-red-color-depend-on-percentage */
    function getGreenToRed(percent){
        var r, g;
        percent = 100 - percent;
        r = percent < 50 ? 255 : Math.floor(255-(percent*2-100)*255/100);
        g = percent > 50 ? 255 : Math.floor((percent*2)*255/100);
        return rgbToHex(r, g, 0);
    }

    /* From http://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb */
    function rgbToHex(r, g, b) {
        return ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }

    function renderMnist(resp) {
        $canvasBag.html('')
        $noiseLabel.html($noiseSlider.val())
        resp.data.forEach(digit => {
            let $canvas = $('<canvas>')
                .attr('width', width)
                .attr('height', height)
            $canvasBag.append($canvas)
            mnist.draw(inverse(digit.flat(2)), $canvas[0].getContext('2d'))
        })
        Object.keys(resp.classifications).forEach(c => {
            let results = resp.classifications[c]
            let accuracy = Math.round(results.accuracy * 100)
            $('#' + c + '-score').html(accuracy + ' %')
            $('#' + c + '-progress').css({
              'width': accuracy + '%',
              'background-color': '#' + getGreenToRed(100-accuracy),
            })
        })
        $spinner.hide()
    }

    // Program start
    let width = 28
    let height = 28
    let batch = 400
    let startingNoise = 0
    let communicating = false

    $noiseLabel.html(startingNoise)
    $noiseSlider.val(startingNoise)
    $noiseSlider.change((evt) => {
        $spinner.show()
        getMnist(batch, $noiseSlider.val(), renderMnist)
    })

    getMnist(batch, startingNoise, renderMnist)
})
