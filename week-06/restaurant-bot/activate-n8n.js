const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

// Find workflow tables
db.all("SELECT name FROM sqlite_master WHERE type='table'", (err, tables) => {
  if (err) { console.log('Error:', err.message); db.close(); return; }
  const wfTables = tables.filter(t => t.name && t.name.toLowerCase().includes('workflow'));
  console.log('Workflow tables:', wfTables.map(t => t.name));
  
  // Check which table has our workflow
  for (const tableName of wfTables) {
    db.all(`SELECT * FROM "${tableName}" WHERE name LIKE '%SpiceRoute%'`, (err, rows) => {
      if (err) { console.log('Query error:', err.message); return; }
      if (rows.length > 0) {
        console.log('Found workflow:', rows[0].name);
        console.log('Current active:', rows[0].active);
        // Activate it
        db.run(`UPDATE "${tableName}" SET active = 1 WHERE name LIKE '%SpiceRoute%'`);
        console.log('Activated!');
        db.close();
      }
    });
  }
});