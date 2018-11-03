$(document).ready(function() {
    var selectedThumbnail = null;
    var thumnailbrowserScrollPosition = $(window).scrollTop();
    const thumbnailClassName = 'show-thumbnailbrowser';
    const editClassName = 'show-edit-overlay';
    const detailClassName = 'show-detail-overlay';
    const collectClassName = 'show-collect-overlay';


    // load artwork data (JSON) and show it in the inspector/sidebar
    updateInspector = function(elInspector, artworkId) {

        // helper function
        // creates elements with optional css classes, text and eventListeners
        function createEl(tagName, cssClassName, text, func) {
            var el = document.createElement(tagName);
            if (cssClassName) el.classList.add(cssClassName);
            if (text) el.appendChild(document.createTextNode(text));
            if (func) el.addEventListener('click', func);
            return el;
        }

        $.getJSON('/artwork/'+artworkId+'.json', function(data) {
            var elDetails = document.createElement('div');
            
            var func = function() { showCollectOverlay(artworkId); }
            elDetails.appendChild(createEl('button', 'inspector-button', 'Merken', func));
            
            func = function() { showEditOverlay(artworkId); }
            elDetails.appendChild(createEl('button', 'inspector-button', 'Edit', func));
            
            $.each( data, function( key, val ) {
                if (!val) return;
                var elKey, elVal;
                var elEntry = document.createElement('div');
                switch (key) {
                    case 'artists':
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
                        elKey = createEl('div', 'key', 'Keywords');
                        elEntry.appendChild(elKey);
                        for (var i = 0; i < val.length; i++) {
                            elVal = createEl('div', 'value', val[i].name, searchForKeyword);
                            elVal.classList.add('tag');
                            elVal.dataset.keyword = val[i].name;
                            elEntry.appendChild(elVal);
                        }
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
        });
    }


    // the page consists of a sidebar and a main view
    // per default, clickable thumbnails are shown
    $('.thumbnail').on('click', function (e) {
        const selectClass = 'selected';
        var clickedThumbnail = e.currentTarget;
        if ($(clickedThumbnail).hasClass(selectClass)) {
            // Clicking a thumbnail twice, shows the detail overlay
            showDetailOverlay(clickedThumbnail.dataset.artworkid);
        } else {
            // Clicking a thumbnail once, selects it and shows the details
            // in the inspector.
            if (selectedThumbnail !== null) {
                $(selectedThumbnail).removeClass(selectClass);
            }
            selectedThumbnail = clickedThumbnail;
            $(selectedThumbnail).addClass(selectClass);
            elInspector = document.getElementById('thumbnailbrowser-inspector');
            updateInspector(elInspector, selectedThumbnail.dataset.artworkid);
        }
    });


    // switch to a specific view
    function showOverlay(classNameToAdd) {
        document.body.className = classNameToAdd;
    }


    // open the detail overlay
    function showDetailOverlay(artworkId) {
        const shownClass = 'shown';
        const url = '/artwork/' + artworkId + '/detail_overlay.html';
        thumnailbrowserScrollPosition = $(window).scrollTop();
        showOverlay(detailClassName);
        $('#detail-overlay').load(url, function() {
            elInspector = document.getElementById('overlay-inspector');
            updateInspector(elInspector, artworkId);            
            $('.image-big').addClass(shownClass);
        });
    }

    // open the detail edit overlay 
    showEditOverlay = function(artworkId) {
        const url = '/artwork/' + artworkId + '/edit_overlay.html';
        // TODO: check if detail overlay open; if not remember scrollPosition
        showOverlay(editClassName);
        $('#edit-overlay').load(url, function() {
            $('.image-big').addClass('shown');
        });
    }

    // open the collect artwork overlay 
    showCollectOverlay = function(artworkId) {
        const userID = 1; // TODO: get userID!
        const url = '/artwork/' + artworkId + '/collect_overlay.html';
        // TODO: check if detail overlay open; if not remember scrollPosition
        showOverlay(collectClassName);
        $('#collect-overlay').load(url, function() {
            elInspector = document.getElementById('overlay-inspector');
            updateInspector(elInspector, artworkId);
        });
    }   


    // close the overlay
    function closeOverlay() {
        document.body.className = thumbnailClassName;
        $(window).scrollTop(thumnailbrowserScrollPosition);
    }


    // hide the detail overlay
    hideDetailOverlay = function() {
        $('.image-big').removeClass('shown');
        closeOverlay();
    };  


    hideEditOverlay = function() {
        // TODO: reload data
        $('.image-big').removeClass('shown');
        closeOverlay();
    };


    // hide the collect artwork overlay
    hideCollectOverlay = function() {
        closeOverlay();
    };


    function searchForKeyword(e) {
        console.log('search for keyword');
        console.log(e.currentTarget.dataset.keyword);
    }

    function searchForArtist(e) {
        console.log('search for artist');
        const artists = e.currentTarget.dataset.artist.replace(/\s/g, "+");
        const url = `?artists=${artists}`;
        console.log(url);
        window.location.href = url;
    }
});