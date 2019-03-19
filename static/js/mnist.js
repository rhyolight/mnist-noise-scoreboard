$(function() {

    let width = 28
    let height = 28
    let batch = 400
    let noise = 0
    // last classification results
    let results

    // DOM stuff used below
    let $spinner = $('.spinner-border')
    let $noiseLabel = $('#noise-label')

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
        $noiseLabel.html(noise + ' %')
        let models = Object.keys(resp.classifications)

        $('.overlay').remove()

        models.forEach((model) => {
            let $canvasBag = $('#' + model + '-canvas-bag')
            $canvasBag.html('')
            resp.data.forEach((digit, i) => {
                let $canvas = $('<canvas>')
                    .attr('id', model + '-digit-' + i)
                    .attr('width', width)
                    .attr('height', height)
                    .attr('data-index', i)
                    .attr('data-target', resp.targets[i])
                    .attr('data-index', i)
                    .addClass('mnist')
                let modelClassifications = results.classifications[model].classifications[i][0]
                $canvas.attr('data-' + model + '-classification', modelClassifications)
                $canvasBag.append($canvas)
                drawMnist(inverse(digit.flat(2)), $canvas, 1)
            })
            highlightModel(model)
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

    function highlightModel(model) {
      let modelResults = results.classifications[model].classifications
      results.targets.forEach((target, i) => {
          let modelGuess = modelResults[i]
          let $canvas = $('#' + model + '-digit-' + i)
          let $overlay = $('<div>').addClass('overlay')
          if (target == modelGuess) {
              $overlay.addClass('correct')
          } else {
              $overlay.addClass('incorrect')
          }
          let topLeft = getOffset($canvas.get(0))
          $overlay.css({top: topLeft.top, left: topLeft.left})
          $('body').append($overlay)
          $overlay.show()
      })
    }

    // Program start

    $noiseLabel.html(noise + ' %')

    function step(newNoise) {
        noise = newNoise
        $.getJSON("/_mnist/" + batch + "/noise/" + noise, (resp) => {
            renderMnist(resp)
            noise++
            if (noise <= 100) {
                step(noise)
            }
        });
    }

    // Kick off the first batch
    step(noise)

})
