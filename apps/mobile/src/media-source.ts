// Only application-relative, source-matched routes may receive an account credential.
export function buildMediaSource(origin: string, path: string, credential: string) {
  if (!/^\/api\/v1\/exercises\/source(?:%3A|:)\d{4}\/media\/(gif|image)$/.test(path)) {
    throw new Error('Invalid application media route');
  }
  const base = new URL(origin);
  if (!['https:', 'http:'].includes(base.protocol) || base.username || base.password || base.search || base.hash || base.pathname !== '/') {
    throw new Error('Invalid API origin');
  }
  if (!credential) throw new Error('Sign in to play this tutorial');
  return {uri: base.origin + path, headers: {Authorization: `Bearer ${credential}`}};
}
