$(function() {

    const CLASSES = ['unknown', 'silence', 'zero', 'one', 'two', 'three',
                     'four', 'five', 'six', 'seven', 'eight', 'nine']

    // DOM stuff used below
    let $canvasBag = $('#canvas-bag')
    let $spinner = $('.spinner-border')

   let $noiseSlider = $('#noise')
   let $noiseLabel = $('#noise-label')
   let $noiseEnabled = $('#noise-enabled')

    // last classification results
    let results

    // Functions

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


    function drawMelSpectrogram(mel, $canvas) {
       let canvas = $canvas[0]
       let context = canvas.getContext('2d')
       var imageData = context.getImageData(0, 0, width, height);
       let greyScale = d3.scaleLinear([-80, 0], [0, 255])
       mel.forEach((slice, s_i) => {
           slice.forEach((db, d_i) => {
               let i = ((d_i * width) + s_i) * 4
               let pixelValue = greyScale(db)
               imageData.data[i] = pixelValue
               imageData.data[i + 1] = pixelValue
               imageData.data[i + 2] = pixelValue
               imageData.data[i + 3] = 255
           })
       })
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

    function renderSpeech(resp) {
        results = resp
        // clearModelHighlight()
        // hideMelDetail()
        $canvasBag.html('')
        $noiseLabel.html($noiseSlider.val())
        resp.data.forEach((mel, i) => {
            let $canvas = $('<canvas>')
                .attr('id', 'mel-' + i)
                .attr('width', width)
                .attr('height', height)
                .attr('data-index', i)
                .attr('data-target', resp.targets[i])
                .attr('data-index', i)
                .addClass('mel')
            $canvasBag.append($canvas)
            drawMelSpectrogram(mel, $canvas)
        })
        let models = Object.keys(resp.classifications)
        Object.keys(resp.classifications).forEach(c => {
            let results = resp.classifications[c]
            let accuracy = Math.round(results.accuracy * 100)
            $('#' + c + '-score').html(accuracy + ' %')
            $('#' + c + '-progress').css({
              'width': accuracy + '%',
              'background-color': '#' + getGreenToRed(100-accuracy),
            })
        })
        // Handle mel interaction
        $('canvas').click(evt => {
            let melIndex = $(evt.currentTarget).attr('id').split('-').pop()
            hideMelDetail()
            showMelDetail(melIndex)
        })
        $spinner.hide()
    }

   function showMelDetail(i) {
       let scale = 6
       let mel = results.data[i]
       let $d = $('<div>').attr('id', 'mel-detail')
       let $c = $('#mel-' + i)
       let topLeft = getOffset($c.get(0))
       let $melCanvas = $('<canvas>')
           .attr('width', 28 * scale)
           .attr('height', 28 * scale)
       let smallCanvas = $c[0]
       $d.css({top: topLeft.top, left: topLeft.left})
       $d.append($melCanvas)
       let $detail = $('<ul>')
       $detail.append('<li>Target: ' + CLASSES[results.targets[i]] + '</li>')
       // $detail.append('<li>Dense CNN: ' + results.classifications.denseCNN1.classifications[i])
       // $detail.append('<li>Sparse CNN: ' + results.classifications.sparseCNN1.classifications[i])
       $d.append($detail)
       let melCanvas = $melCanvas.get(0)
       let largeContext = melCanvas.getContext('2d')
       var largeMel = new Image();
       largeMel.onload = function(){
           largeContext.clearRect(0, 0, melCanvas.width, melCanvas.height);
           largeContext.scale(scale, scale);
           largeContext.drawImage(largeMel, 0, 0);
       }
       // Loads the small mnist canvas data into new image.
       largeMel.src = smallCanvas.toDataURL();

       drawMelSpectrogram(mel, $melCanvas)
       $('body').append($d)

       let path = results.paths[i]
       let target = results.targets[i]
       if (path) {
           let parts = path.split(/\//)
           let targetName = parts[4]
           let targetIndex = CLASSES.indexOf(targetName)
           let filename = parts[5]
           let originalUrl = '/_wavs/original/' + targetName + '/' + filename
           let augUrl = '/_wavs/augmented/' + targetIndex + '/' + filename
           var audio = new Audio(augUrl)
           audio.play()
       }
   }

   function hideMelDetail() {
       $('#mel-detail').remove()
   }

   function clearModelHighlight() {
       $('.overlay').remove()
       $('.model').removeClass('highlight')
   }

   function highlightModel(model) {
     hideMelDetail()
     let modelResults = results.classifications[model].classifications
     $('#' + model).addClass('highlight')
     results.targets.forEach((target, i) => {
         let modelGuess = modelResults[i]
         let $c = $('#mel-' + i)
         let $o = $('<div>').addClass('overlay').addClass('mel')
         if (target == modelGuess) {
             $o.addClass('correct')
         } else {
             $o.addClass('incorrect')
         }
         let topLeft = getOffset($c.get(0))
         $o.css({top: topLeft.top, left: topLeft.left})
         // Handle mel interaction
         $o.click(evt => {
             hideMelDetail()
             showMelDetail(i)
         })
         $('body').append($o)
         $o.show()
     })
   }

   let startingNoise = 0
   let communicating = false

   // Handle noise interaction
   $noiseLabel.html(startingNoise)
   $noiseSlider.val(startingNoise)
   $noiseSlider.change((evt) => {
       if ($noiseEnabled.is(':checked')) {
           $spinner.show()
           $.getJSON("/_speech/" + batch + "/noise/" + $noiseSlider.val(), renderSpeech);
       }
   })

//    // Transform Activation
//    $('input[type=radio]').change((evt) => {
//        let $radio = $(evt.currentTarget)
//        let xform = $radio.attr('id').split('-').shift()
//        let $slider = $('#' + xform)
//        $('input[type=radio]').prop('checked', false)
//        $('#' + xform + '-enabled').prop('checked', true)
//        $spinner.show()
//        let val = $slider.val()
//        if (! val) val = 0
//        $.getJSON("/_mnist/" + batch + "/" + xform + "/" + val, renderMnist);
//    })

   // Handle Model interaction
   $('.model').hover(evt => {
       let model = $(evt.currentTarget).attr('id')
       clearModelHighlight()
       hideMelDetail()
       highlightModel(model)
   })

    // Program start
    let batch = 300
    let width = 32
    let height = 32

    // Kick off the first batch
    $.getJSON(
        "/_speech/" + batch + "/noise/" + startingNoise, renderSpeech
    )
})
