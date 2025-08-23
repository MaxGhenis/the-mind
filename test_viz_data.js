// Test the data parsing issue
const Papa = require('papaparse');
const fs = require('fs');

// Read the sample data
const csvText = fs.readFileSync('visualization/public/sample_data.csv', 'utf8');

// Parse with dynamicTyping like the app does
Papa.parse(csvText, {
  header: true,
  dynamicTyping: true,
  complete: (results) => {
    console.log('Parsed data sample:');
    const firstRow = results.data[0];
    console.log('First row:', firstRow);
    console.log('cards_played type:', typeof firstRow.cards_played);
    console.log('cards_played value:', firstRow.cards_played);
    
    // Try to parse it
    try {
      if (typeof firstRow.cards_played === 'string') {
        const parsed = JSON.parse(firstRow.cards_played);
        console.log('Successfully parsed:', parsed);
      } else {
        console.log('Already parsed as:', firstRow.cards_played);
      }
    } catch (e) {
      console.error('Parse error:', e.message);
    }
  }
});