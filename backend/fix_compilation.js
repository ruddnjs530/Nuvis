const fs = require('fs');
const path = require('path');

const domains = ['auth', 'room', 'robot', 'event', 'schedule'];
const baseDir = path.join(__dirname, 'src', 'modules');

domains.forEach(domain => {
  const servicePath = path.join(baseDir, domain, 'services', domain + '.service.ts');
  if (fs.existsSync(servicePath)) {
    let content = fs.readFileSync(servicePath, 'utf8');
    if (!content.includes('create(data: any)')) {
      content = content.replace(/}\s*$/, "\n  create(data: any) { return null; }\n}\n");
      fs.writeFileSync(servicePath, content);
      console.log('Fixed ' + servicePath);
    }
  }
});
