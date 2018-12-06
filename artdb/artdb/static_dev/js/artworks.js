$(document).ready(function() {
    var selectedThumbnail = null;
    var thumbnailbrowserScrollPosition = $(window).scrollTop();
    const thumbnailClassName = 'show-thumbnailbrowser';
    const editClassName = 'show-edit-overlay';
    const detailClassName = 'show-detail-overlay';
    const collectClassName = 'show-collect-overlay';


    // load artwork data (JSON) and show it in the inspector/sidebar
    updateInspector = function(elInspector, artworkID) {
        // helper function
        // creates elements with optional css classes, text and eventListeners
        function createEl(tagName, cssClassName, text, func) {
            var el = document.createElement(tagName);
            if (cssClassName) el.classList.add(cssClassName);
            if (text) el.appendChild(document.createTextNode(text));
            if (func) el.addEventListener('click', func);
            return el;
        }

        $.getJSON('/artwork/'+artworkID+'.json', function(data) {
            var elDetails = document.createElement('div');
            
            var func = function() { showCollectOverlay(artworkID); }
            elDetails.appendChild(createEl('button', 'inspector-button', 'Merken', func));
            
            func = function() { showEditOverlay(artworkID); }
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
                        elVal.dataset.keyword = val.name;
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
        // remember the scroll position
        if ($('body').hasClass(thumbnailClassName)) {
            thumbnailbrowserScrollPosition = $(window).scrollTop();
            window.scrollTo(0, 0);
        }
        document.body.className = classNameToAdd;
    }


    // open the detail overlay
    function showDetailOverlay(artworkID) {
        const url = '/artwork/' + artworkID + '/detail_overlay.html';
        showOverlay(detailClassName);
        $('#detail-overlay').load(url, function() {
            elInspector = document.getElementById('detail-overlay-inspector');
            updateInspector(elInspector, artworkID);       
            $('.image-big').addClass('shown');
        });
    }

    // open the collect artwork overlay 
    showCollectOverlay = function(artworkID) {
        const url = '/artwork/' + artworkID + '/collect_overlay.html';
        showOverlay(collectClassName);
        $('#collect-overlay').load(url, function() {
            console.log("loaded");
            elInspector = document.getElementById('collect-overlay-inspector');
            updateInspector(elInspector, artworkID);
        });
    }

    // open the detail edit overlay 
    showEditOverlay = function(artworkID) {
        const url = '/artwork/' + artworkID + '/edit_overlay.html';
        showOverlay(editClassName);
        $('#edit-overlay').load(url, function() {
            $('.image-big').addClass('shown');
        });
    }

    // close the overlay
    function closeOverlay() {
        document.body.className = thumbnailClassName;
        $(window).scrollTop(thumbnailbrowserScrollPosition);
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
        console.log(e.currentTarget.dataset.keyword);
    }

    function searchForLocation(e) {
        console.log(e.currentTarget.dataset.keyword);
    }

    function searchForArtist(e) {
        const artists = e.currentTarget.dataset.artist.replace(/\s/g, "+");
        const url = `?artists=${artists}`;
        console.log(url);
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
            $('#search-basic').addClass('fadeout');
            $('#search-basic').one('transitionend', function() {
                $('#search-basic').addClass('hidden');
            });
            $('#search-expert').removeClass('hidden');
            $('#search-expert-fold').addClass('unfolded');
            $('#search-expert-fold').one('transitionend', function() {
                $('#search-expert').removeClass('hidden');
                $('#search-expert').removeClass('fadeout');
            });
        } else {
            $('#search-expert').addClass('fadeout');
            $('#search-expert-fold').removeClass('unfolded');
            $('#search-expert-fold').one('transitionend', function() {
                $('#search-expert').addClass('hidden');
                $('#search-basic').removeClass('hidden');
                $('#search-basic').removeClass('fadeout'); 
            });
        }
    }); 
});