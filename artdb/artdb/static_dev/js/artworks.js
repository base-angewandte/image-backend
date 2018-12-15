$(document).ready(function() {
    var selectedThumbnail = null;
    var thumbnailbrowserScrollPosition = $(window).scrollTop();
    var elCurrentInspector = null;
    const thumbnailClassName = 'show-thumbnailbrowser';
    const editClassName = 'show-edit-overlay';
    const detailClassName = 'show-detail-overlay';
    const collectClassName = 'show-collect-overlay';
    var bSmallTopbar = false;

    // load artwork data (JSON) and show it in the inspector/sidebar
    updateInspector = function(elInspector, url) {
        // helper function
        // creates elements with optional css classes, text and eventListeners
        function createEl(tagName, cssClassName, text, func) {
            var el = document.createElement(tagName);
            if (cssClassName) el.classList.add(cssClassName);
            if (text) el.appendChild(document.createTextNode(text));
            if (func) el.addEventListener('click', func);
            return el;
        }

        const jsonUrl = url + '.json';
        $.getJSON(jsonUrl, function(data) {
            var elDetails = document.createElement('div');
            
            var func = function() { showCollectOverlay(url); }
            elDetails.appendChild(createEl('button', 'inspector-button', 'Merken', func));
            
            func = function() { showEditOverlay(url); }
            elDetails.appendChild(createEl('button', 'inspector-button', 'Edit', func));
            
            // build all the elements and append them to the DOM 
            $.each( data, function( key, val ) {
                if (!val) return;
                var elKey, elVal;
                var elEntry = document.createElement('div');
                console.log(key);
                switch (key) {
                    case 'artists':
                        if (val.length === 0) break;
                        elKey = createEl('div', 'key', 'Artist');
                        elEntry.appendChild(elKey);
                        for (var i = 0; i < val.length; i++) {
                            elVal = createEl('div', 'value', val[i].name, searchForArtist);
                            elVal.classList.add('tag');
                            elVal.dataset.artist = val[i].name;
                            elEntry.appendChild(elVal);
                        }
                        break;
                    case 'keywords':
                        if (val.length === 0) break;
                        elKey = createEl('div', 'key', 'Keywords');
                        elEntry.appendChild(elKey);
                        for (var i = 0; i < val.length; i++) {
                            elVal = createEl('div', 'value', val[i].name, searchForKeyword);
                            elVal.classList.add('tag');
                            elVal.dataset.keyword = val[i].name;
                            elEntry.appendChild(elVal);
                        }
                        break;
                    case 'locationOfCreation':
                        if (val.length === 0) break;
                        elKey = createEl('div', 'key', 'LocationOfCreation');
                        elEntry.appendChild(elKey);
                        elVal = createEl('div', 'value', val.name, searchForLocation);
                        elVal.classList.add('tag');
                        elVal.dataset.location = val.name;
                        elEntry.appendChild(elVal);
                        break;
                    default:
                        if ((val !== '') && (val !== null)) {
                            elKey = createEl('div', 'key', key);
                            elEntry.appendChild(elKey);
                            elVal = createEl('div', 'value', val);
                            if (key === 'titleEnglish') {
                                elKey.classList.add('key-titleEnglish');
                                elVal.classList.add('val-titleEnglish');
                            }
                            elEntry.appendChild(elVal);
                        }
                }
                elDetails.appendChild(elEntry);
            }); 
            elInspector.replaceChild(elDetails, elInspector.getElementsByTagName('div')[0]);
            elCurrentInspector = elInspector;
        });
    }

    // the page consists of a sidebar and a main view
    // per default, clickable thumbnails are shown
    $('.thumbnail').on('click', function (e) {
        const selectClass = 'selected';
        var clickedThumbnail = e.currentTarget;
        if ($(clickedThumbnail).hasClass(selectClass)) {
            // Clicking a thumbnail twice, shows the detail overlay
            showDetailOverlay(clickedThumbnail.dataset.url);
        } else {
            // Clicking a thumbnail once, selects it and shows the details
            // in the inspector.
            if (selectedThumbnail !== null) {
                $(selectedThumbnail).removeClass(selectClass);
            }
            selectedThumbnail = clickedThumbnail;
            $(selectedThumbnail).addClass(selectClass);
            elInspector = document.getElementById('thumbnailbrowser-inspector');
            updateInspector(elInspector,  selectedThumbnail.dataset.url);
        }
    });

    // hide the collect artwork overlay
    hideCollectOverlay = function() {
        closeOverlay();
    };

    // hide the detail or edit overlay
    hideImageAndOverlay = function() {
        $('.image-big').removeClass('shown');
        closeOverlay();
    };  

    // copy the content from one inspector to another
    // this avoids unnecessary reloads
    function copyInspectorDetails(elNewInspector) {
        elCurrentDetails = elCurrentInspector.getElementsByTagName('div')[0].cloneNode(true);
        elNewInspector.replaceChild(elCurrentDetails, elNewInspector.getElementsByTagName('div')[0]);
        elCurrentInspector = elNewInspector;
    }

    // hide the overlay
    function closeOverlay() {
        var elNewInspector = document.getElementById('thumbnailbrowser-inspector');
        copyInspectorDetails(elNewInspector);
        document.body.className = thumbnailClassName;
        window.scrollTo(0,thumbnailbrowserScrollPosition);
    }

    // show a specific overlay
    function showOverlay(classNameToAdd) {
        if ($('body').hasClass(thumbnailClassName)) {
            // remember the scroll position
            thumbnailbrowserScrollPosition = $(window).scrollTop();
            document.body.className = classNameToAdd;
            window.scrollTo(0, 0);
        } else {
            document.body.className = classNameToAdd;
        }
    }

    // show the detail overlay
    function showDetailOverlay(url) {
        overlayUrl = url + '/detail_overlay.html';
        $('#detail-overlay').load(overlayUrl, function() {
            var elInspector = document.getElementById('detail-overlay-inspector');
            copyInspectorDetails(elInspector);
            $('.image-big').addClass('shown');
            showOverlay(detailClassName);
        });
    }

    // show the collect artwork overlay 
    showCollectOverlay = function(url) {
        overlayUrl = url + '/collect_overlay.html';
        $('#collect-overlay').load(overlayUrl, function() {
            elInspector = document.getElementById('collect-overlay-inspector');
            copyInspectorDetails(elInspector);
            showOverlay(collectClassName);
        });
    }

    // show the detail edit overlay
    showEditOverlay = function(url) {
        overlayUrl = url + '/edit_overlay.html';
        $('#edit-overlay').load(overlayUrl, function() {
            $('.image-big').addClass('shown');
            showOverlay(editClassName);
        });
    }

    function searchForKeyword(e) {
        const keyword = e.currentTarget.dataset.keyword.replace(/\s/g, "+");
        const url = `?keyword=${keyword}`;
        window.location.href = url;
    }

    function searchForLocation(e) {
        const location = e.currentTarget.dataset.location.replace(/\s/g, "+");
        const url = `?location=${location}`;
        window.location.href = url;
    }

    function searchForArtist(e) {
        const artist = e.currentTarget.dataset.artist.replace(/\s/g, "+");
        const url = `?artist=${artist}`;
        window.location.href = url;
    }

    // do not submit empty form fields
    $("#search-expert").submit(function() {
        $(this).find(":input").filter(function() { return !this.value; }).attr("disabled", "disabled");
        return true;
    });
    $("form" ).find(":input").prop("disabled", false);

    // search basic/expert switch
    $("#js-search-switch").click(function(e) {
        if ($(this).prop('checked')) {
            // switching to expert search
            $('#search-basic').addClass('fadeout')
            .one('transitionend', function() {
                $('#search-basic').addClass('hidden');
            });
            $('#search-expert').removeClass('hidden');
            $('#search-expert-fold').addClass('unfolded')
            .one('transitionend', function() {
                $('#search-expert').removeClass('fadeout');
            });
        } else {
            // switching to basic search
            $('#search-basic').removeClass('hidden');
            $('#search-expert').addClass('fadeout');
            $('#search-expert-fold').removeClass('unfolded')
            .one('transitionend', function() {
                //$('#search-expert').addClass('hidden');
                $('#search-basic').removeClass('fadeout'); 
            });
        }
    });
    
    window.addEventListener('scroll', throttle(handleScroll, 30));

    function handleScroll() {
        if (window.pageYOffset >= 32) {
            $('#topbar').addClass('small');
            $('.button-close').addClass('fixed');
            bSmallTopbar = true;
        } else {
            if (bSmallTopbar) {
                $('#topbar').removeClass('small');
                $('.button-close').removeClass('fixed');
                bSmallTopbar = false;
            }
        }
    }

    function throttle(callback) {
        var active = false; // a simple flag
        var evt; // to keep track of the last event
        var handler = function(){ // fired only when screen has refreshed
          active = false; // release our flag 
          callback(evt);
          }
        return function handleEvent(e) { // the actual event handler
          evt = e; // save our event at each call
          if (!active) { // only if we weren't already doing it
            active = true; // raise the flag
            requestAnimationFrame(handler); // wait for next screen refresh
          };
        }
    }
});