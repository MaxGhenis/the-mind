const Papa = require('papaparse');
const fs = require('fs');

// Read and parse the CSV
const csvText = fs.readFileSync('visualization/public/sample_data.csv', 'utf8');

Papa.parse(csvText, {
  header: true,
  dynamicTyping: true,
  complete: (results) => {
    const data = results.data[0];
    console.log('Parsed data:');
    console.log('success field:', data.success);
    console.log('success type:', typeof data.success);
    console.log('success == false:', data.success == false);
    console.log('success === false:', data.success === false);
    console.log('!success:', !data.success);
    console.log('\nFull row:', data);
  }
});