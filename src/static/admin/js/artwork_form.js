window.addEventListener('load', function () {
  const $ = django.jQuery;

  function processDimensions() {
    const $dimensions_display = $('#id_dimensions_display');
    const width = $('#id_width').val();
    const height = $('#id_height').val();
    const depth = $('#id_depth').val();

    // TODO: discuss whether this is the preferred conditional rendering of the dimensions
    //   and whether we should always overwrite the dimensions_display field
    if (width && height) {
      let dimensions = `${width} x ${height}`;
      if (depth) dimensions += ` x ${height}`;
      dimensions += ' cm';
      $dimensions_display.val(dimensions);
    }
  }
  $('#id_width').keyup(processDimensions);
  $('#id_height').keyup(processDimensions);
  $('#id_depth').keyup(processDimensions);

  $('#id_date').keyup(function () {
    function updateInputFields(yearFrom, yearTo) {
      yearFrom = parseInt(yearFrom);
      if (yearTo) {
        yearTo = parseInt(yearTo);
      } else {
        yearTo = yearFrom;
      }
      switch (preposition) {
        case 'ca.':
        case 'um':
          yearFrom -= 5;
          yearTo += 5;
          break;
        case 'vor':
          yearFrom -= 5;
          break;
        case 'nach':
          yearTo += 5;
          break;
      }
      $('#id_date_year_from').val(yearFrom);
      $('#id_date_year_to').val(yearTo);
    }

    var regexp, matchedParts, preposition;
    var userinput = $('#id_date').val().replace(/ /g, ''); // remove spaces

    // detect prepositions
    regexp = /^(ca\.|um|vor|nach|Ende|Anfang)(.*)/;
    matchedParts = userinput.match(regexp);
    if (matchedParts) {
      if (matchedParts.length > 1) {
        preposition = matchedParts[1];
        userinput = matchedParts[2];
      }
    }

    // detect year range: e.g. "1921-1923","-20000-0", "1943/1972"
    regexp = /^([-]?\d{1,5})[-/]([-]?\d{1,5})$/;
    matchedParts = userinput.match(regexp);
    if (matchedParts) {
      updateInputFields(matchedParts[1], matchedParts[2]);
      return;
    }

    // detect date and date (DD.MM.YYYY) range: "5.3.1799", "24.10.1929-28.19.1929"
    regexp = /^\d{1,2}\.\d{1,2}\.(\d{1,4})(-\d{1,2}\.\d{1,2}\.(\d{1,4}))?$/;
    matchedParts = userinput.match(regexp);
    if (matchedParts) {
      var from = matchedParts[1];
      var to = from;
      if (matchedParts[3]) {
        to = matchedParts[3];
      }
      updateInputFields(from, to);
      return;
    }

    // century and century range: "14.Jh.", "13.Jh.-14.Jh.", "Ende 14.Jh."
    regexp = /^(\d{1,2})\.Jh\.(-(\d{1,2})\.Jh\.)?$/;
    matchedParts = userinput.match(regexp);
    if (matchedParts) {
      var from, to;
      if (preposition === 'Anfang') {
        from = ((matchedParts[1] - 1) * 100) + 1;
        to = from + 15;
      } else if (preposition === 'Ende') {
        to = ((matchedParts[1] - 1) * 100) + 100;
        from = to - 15;
      } else if (matchedParts[3]) {
        from = ((matchedParts[1] - 1) * 100) + 1;
        to = (matchedParts[3] * 100);
      } else {
        from = ((matchedParts[1] - 1) * 100) + 1;
        to = from + 99;
      }
      updateInputFields(from, to);
      return;
    }

    // detect year
    regexp = /(^[-]?\d{1,5})$/;
    matchedParts = userinput.match(regexp);
    if (matchedParts) {
      updateInputFields(matchedParts[1], matchedParts[1]);
      return;
    }

  });
}, false);
