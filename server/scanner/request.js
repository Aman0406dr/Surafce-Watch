import dns from 'node:dns/promises';
import http from 'node:http';
import https from 'node:https';
import ipaddr from 'ipaddr.js';

const MAX_RESPONSE_BYTES = 512 * 1024;
const MAX_REDIRECTS = 3;
const REQUEST_TIMEOUT_MS = 10_000;

function isPublicAddress(address) {
  try {
    return ipaddr.parse(address).range() === 'unicast';
  } catch {
    return false;
  }
}

async function getPublicAddress(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    throw new Error('Enter a valid URL with a hostname.');
  }

  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('Only http:// and https:// URLs can be scanned.');
  }
  if (parsed.username || parsed.password || !parsed.hostname) {
    throw new Error('Enter a public website URL without embedded credentials.');
  }

  const hostname = parsed.hostname.replace(/^\[|\]$/g, '').replace(/\.$/, '');
  if (hostname.toLowerCase() === 'localhost' || hostname.toLowerCase().endsWith('.localhost')) {
    throw new Error('Localhost and private network destinations are not allowed.');
  }

  let addresses;
  try {
    const literal = ipaddr.parse(hostname);
    addresses = [{ address: literal.toString(), family: literal.kind() === 'ipv4' ? 4 : 6 }];
  } catch {
    try {
      addresses = await dns.lookup(hostname, { all: true, verbatim: true });
    } catch {
      throw new Error('The hostname could not be resolved.');
    }
  }

  if (!addresses.length || addresses.some(({ address }) => !isPublicAddress(address))) {
    throw new Error('Localhost and private network destinations are not allowed.');
  }

  const address = addresses.find(candidate => candidate.family === 4) || addresses[0];
  return { parsed, hostname, address };
}

function requestPage(url, hostname, address) {
  const transport = url.protocol === 'https:' ? https : http;

  return new Promise((resolve, reject) => {
    let finished = false;
    const finish = (error, result) => {
      if (finished) return;
      finished = true;
      if (error) reject(error);
      else resolve(result);
    };

    const request = transport.request(url, {
      method: 'GET',
      headers: {
        'User-Agent': 'SurfaceWatch/1.0 (passive security header audit)',
        Accept: 'text/html,application/xhtml+xml,*/*;q=0.5',
        Connection: 'close',
      },
      rejectUnauthorized: true,
      servername: hostname,
      lookup(_hostname, options, callback) {
        const result = { address: address.address, family: address.family };
        if (options?.all) callback(null, [result]);
        else callback(null, result.address, result.family);
      },
    }, response => {
      const chunks = [];
      let size = 0;

      response.on('data', chunk => {
        if (finished) return;

        const remaining = MAX_RESPONSE_BYTES - size;
        if (chunk.length > remaining) {
          if (remaining > 0) chunks.push(chunk.subarray(0, remaining));
          size = MAX_RESPONSE_BYTES;
          finish(null, {
            statusCode: response.statusCode || 0,
            headers: response.headers,
            body: Buffer.concat(chunks, size),
          });
          response.destroy();
          return;
        }

        chunks.push(chunk);
        size += chunk.length;
      });

      response.on('end', () => finish(null, {
        statusCode: response.statusCode || 0,
        headers: response.headers,
        body: Buffer.concat(chunks, size),
      }));
      response.on('error', error => finish(error));
    });

    request.setTimeout(REQUEST_TIMEOUT_MS, () => request.destroy(new Error('The request timed out.')));
    request.on('error', error => finish(new Error(`Could not fetch the site: ${error.message}`)));
    request.end();
  });
}

export async function fetchPage(target) {
  let currentUrl = target;
  const redirects = [];

  for (let count = 0; count <= MAX_REDIRECTS; count += 1) {
    const { parsed, hostname, address } = await getPublicAddress(currentUrl);
    const response = await requestPage(parsed, hostname, address);

    if (![301, 302, 303, 307, 308].includes(response.statusCode)) {
      return { ...response, finalUrl: parsed.href, redirects };
    }

    const location = response.headers.location;
    if (!location) throw new Error('The site returned a redirect without a destination.');
    if (count === MAX_REDIRECTS) throw new Error('The site redirected too many times.');

    currentUrl = new URL(location, parsed).href;
    redirects.push(currentUrl);
  }

  throw new Error('The site did not return a response.');
}
