## written by Bianca Tong and Wayne for comp9331 ass2
#include <stdbool.h>

typedef char Vertex;
typedef struct Edge
{
   Vertex v;
   Vertex w;
   int delay;
   int capacity;
   int count;
} Edge;
typedef struct GraphRep
{
   Edge **edges;
   int nV;
   int nE;
} GraphRep;
typedef struct GraphRep *Graph;

Graph createGraph(void);
void  insertEdge(Graph, Edge, int i, int j);
void  freeGraph(Graph);
