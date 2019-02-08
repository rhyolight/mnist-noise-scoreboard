
$(function() {

    // DOM stuff used below
    let $canvasBag = $('#canvas-bag')
    let $noiseSlider = $('#noise')
    let $noiseLabel = $('#noise-label')

    // Functions

    function inverse(array) {
        return array.map(i => { return 1.0 - i })
    }

    function getMnist(batch, noise, cb) {
      $.getJSON("/_mnist/" + batch + "/" + noise, cb);
    }

    function highlightWinner() {

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
            $('#' + c + '-progress').css('width', accuracy + '%')
        })
    }

    // Program start
    let width = 28
    let height = 28
    let batch = 400
    let startingNoise = 15
    let communicating = false

    $noiseLabel.html(startingNoise)
    $noiseSlider.val(startingNoise)
    $noiseSlider.change((evt) => {
        getMnist(batch, $noiseSlider.val(), renderMnist)
    })

    getMnist(batch, startingNoise, renderMnist)
})
