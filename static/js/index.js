$(function() {

    // DOM stuff used below
    let $canvasBag = $('#canvas-bag')
    let $noiseSlider = $('#noise')
    let $noiseLabel = $('#noise-label')
    let $noiseEnabled = $('#noise-enabled')
    let $gridSlider = $('#grid-size')
    let $gridLabel = $('#grid-size-label')
    let $gridEnabled = $('#grid-enabled')
    let $wipeSlider = $('#wipe-perc')
    let $wipeLabel = $('#wipe-perc-label')
    let $wipeEnabled = $('#wipe-enabled')
    let $spinner = $('.spinner-border')

    // last classification results
    let results

    // Functions

    function drawMnist(digit, $canvas) {
        let canvas = $canvas[0]
        let context = canvas.getContext('2d')
        var imageData = context.getImageData(0, 0, 28, 28);
        for (var i = 0; i < digit.length; i++) {
            imageData.data[i * 4] = digit[i] * 255;
            imageData.data[i * 4 + 1] = digit[i] * 255;
            imageData.data[i * 4 + 2] = digit[i] * 255;
            imageData.data[i * 4 + 3] = 255;
        }
        context.putImageData(imageData, 0, 0);
    }

    function getOffset( el ) {
        var _x = 0;
        var _y = 0;
        while( el && !isNaN( el.offsetLeft ) && !isNaN( el.offsetTop ) ) {
            _x += el.offsetLeft - el.scrollLeft;
            _y += el.offsetTop - el.scrollTop;
            el = el.offsetParent;
        }
        return { top: _y, left: _x };
    }

    function inverse(array) {
        return array.map(i => { return 1.0 - i })
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
        results = resp
        clearModelHighlight()
        hideDigitDetail()
        $canvasBag.html('')
        $noiseLabel.html($noiseSlider.val())
        $gridLabel.html($gridSlider.val())
        $wipeLabel.html($wipeSlider.val())
        let models = Object.keys(resp.classifications)
        resp.data.forEach((digit, i) => {
            let $canvas = $('<canvas>')
                .attr('id', 'digit-' + i)
                .attr('width', width)
                .attr('height', height)
                .attr('data-index', i)
                .attr('data-target', resp.targets[i])
                .attr('data-index', i)
                .addClass('mnist')
            models.forEach(m => {
                let modelClassifications = results.classifications[m].classifications[i][0]
                $canvas.attr('data-' + m + '-classification', modelClassifications)
            })
            $canvasBag.append($canvas)
            drawMnist(inverse(digit.flat(2)), $canvas, 1)
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
        // Handle digit interaction
        $('canvas').click(evt => {
            let digitIndex = $(evt.currentTarget).attr('id').split('-').pop()
            hideDigitDetail()
            showDigitDetail(digitIndex)
        })
        $spinner.hide()
    }

    function showDigitDetail(i) {
        let scale = 6
        let digit = results.data[i]
        let $d = $('<div>').attr('id', 'digit-detail')
        let $c = $('#digit-' + i)
        let topLeft = getOffset($c.get(0))
        let $digitCanvas = $('<canvas>')
            .attr('width', 28 * scale)
            .attr('height', 28 * scale)
        let smallCanvas = $c[0]
        $d.css({top: topLeft.top, left: topLeft.left})
        $d.append($digitCanvas)
        let digitCanvas = $digitCanvas.get(0)
        let largeContext = digitCanvas.getContext('2d')
        var largeDigit = new Image();
        largeDigit.onload = function(){
            largeContext.clearRect(0, 0, digitCanvas.width, digitCanvas.height);
            largeContext.scale(scale, scale);
            largeContext.drawImage(largeDigit, 0, 0);
        }
        // Loads the small mnist canvas data into new image.
        largeDigit.src = smallCanvas.toDataURL();

        drawMnist(inverse(digit.flat(2)), $digitCanvas)
        $('body').append($d)
    }

    function hideDigitDetail() {
        $('#digit-detail').remove()
    }

    function clearModelHighlight() {
        $('.overlay').remove()
        $('.model').removeClass('highlight')
    }

    function highlightModel(model) {
      hideDigitDetail()
      let modelResults = results.classifications[model].classifications
      $('#' + model).addClass('highlight')
      results.targets.forEach((target, i) => {
          let modelGuess = modelResults[i]
          let $c = $('#digit-' + i)
          let $o = $('<div>').addClass('overlay')
          if (target == modelGuess) {
              $o.addClass('correct')
          } else {
              $o.addClass('incorrect')
          }
          let topLeft = getOffset($c.get(0))
          $o.css({top: topLeft.top, left: topLeft.left})
          // Handle digit interaction
          $o.click(evt => {
              hideDigitDetail()
              showDigitDetail(i)
          })
          $('body').append($o)
          $o.show()
      })
    }

    // Program start
    let width = 28
    let height = 28
    let batch = 400
    let startingNoise = 0
    let communicating = false

    // Handle noise interaction
    $noiseLabel.html(startingNoise)
    $noiseSlider.val(startingNoise)
    $noiseSlider.change((evt) => {
        if ($noiseEnabled.is(':checked')) {
            $spinner.show()
            $.getJSON("/_mnist/" + batch + "/RandomNoise/" + $noiseSlider.val(), renderMnist);
        }
    })

    // Handle Grid Size interaction
    $gridLabel.html(0)
    $gridSlider.val(0)
    $gridSlider.change((evt) => {
        if ($gridEnabled.is(':checked')) {
            $spinner.show()
            $.getJSON("/_mnist/" + batch + "/Grid/" + $gridSlider.val(), renderMnist);
        }
    })

    // Handle Wipe interaction
    $wipeLabel.html(0)
    $wipeSlider.val(0)
    $wipeSlider.change((evt) => {
        if ($wipeEnabled.is(':checked')) {
            $spinner.show()
            $.getJSON("/_mnist/" + batch + "/Wipe/" + $wipeSlider.val(), renderMnist);
        }
    })

    // Handle Model interaction
    $('.model').hover(evt => {
        let model = $(evt.currentTarget).attr('id')
        clearModelHighlight()
        hideDigitDetail()
        highlightModel(model)
    })

    // Kick off the first batch
    $.getJSON("/_mnist/" + batch + "/RandomNoise/" + startingNoise, renderMnist);
})
