// A89 specialized exact token automaton. Classic reachability and shortest paths.
#include <algorithm>
#include <cstdint>
#include <functional>
#include <queue>
#include <vector>
static int S, C;
static std::vector<int> T;
static std::vector<std::vector<int>> adj, rev;
static constexpr int INF=10000;
extern "C" {
void init(int s,int c,const int* t) {
 S=s; C=c; T.assign(t,t+s*c); adj.assign(s,{});rev.assign(s,{});
 for(int u=0;u<S;u++) {
  for(int k=0;k<C;k++) if(T[k*S+u]>=0) adj[u].push_back(T[k*S+u]);
  std::sort(adj[u].begin(),adj[u].end());
  adj[u].erase(std::unique(adj[u].begin(),adj[u].end()),adj[u].end());
  for(int v:adj[u]) rev[v].push_back(u);
 }
}
void distances(int* d) {
 for(int u=0;u<S;u++) {
  int* r=d+u*S;std::fill(r,r+S,INF);r[u]=0;
  std::queue<int> q;q.push(u);
  while(!q.empty()){int v=q.front();q.pop();for(int w:adj[v])if(r[w]==INF){r[w]=r[v]+1;q.push(w);}}
 }
}
void build(int n,const int* x,int changed,uint8_t* f,uint8_t* b) {
 if(changed<0){std::fill(f,f+(n+1)*S,0);std::fill(b,b+(n+1)*S,0);f[0]=1;b[n*S+S-1]=1;changed=0;}
 for(int i=changed;i<n;i++) {
  auto out=f+(i+1)*S;std::fill(out,out+S,0);
  for(int u=0;u<S;u++) if(f[i*S+u]) {
   if(x[i]<0)for(int v:adj[u])out[v]=1;
   else {int v=T[x[i]*S+u];if(v>=0)out[v]=1;}
  }
 }
 int start=(changed==0?n-1:changed);
 for(int i=start;i>=0;i--) {
  auto out=b+i*S;std::fill(out,out+S,0);
  for(int u=0;u<S;u++) {
   if(x[i]<0){for(int v:adj[u])if(b[(i+1)*S+v]){out[u]=1;break;}}
   else {int v=T[x[i]*S+u];if(v>=0)out[u]=b[(i+1)*S+v];}
  }
 }
}
int allows(int pos,int cls,const uint8_t* f,const uint8_t* b) {
 for(int u=0;u<S;u++)if(f[pos*S+u]){int v=T[cls*S+u];if(v>=0&&b[(pos+1)*S+v])return 1;}
 return 0;
}
void allocation(int n,const int* x,int* d) {
 using P=std::pair<int,int>;
 for(int i=n;i>=0;i--) {
  int* out=d+i*S;
  std::fill(out,out+S,INF);
  if(i==n)out[S-1]=0;
  else for(int u=0;u<S;u++) {
   if(x[i]<0)for(int v:adj[u])out[u]=std::min(out[u],d[(i+1)*S+v]);
   else {int v=T[x[i]*S+u];if(v>=0)out[u]=d[(i+1)*S+v];}
  }
  std::priority_queue<P,std::vector<P>,std::greater<P>> q;
  for(int u=0;u<S;u++)if(out[u]<INF)q.push({out[u],u});
  while(!q.empty()) {
   auto [cost,v]=q.top();q.pop();if(cost!=out[v])continue;
   for(int u:rev[v])if(out[u]>cost+1){out[u]=cost+1;q.push({cost+1,u});}
  }
 }
}
}
