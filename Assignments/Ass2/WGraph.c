## written by Bianca Tong and Wayne for comp9331 ass2
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include "WGraph.h"

Graph createGraph(void)
{
	/* malloc space for graph */
    Graph g=malloc(sizeof(GraphRep));
    assert(g!=NULL);
    g->nV=26;
    g->nE=0;
    /* malloc space for row */
    g->edges=malloc(26*sizeof(Edge*));
    assert(g->edges!=NULL);
	int i,j;
    for(i=0;i<26;i++)
    {
    	/* malloc space for column */
    	g->edges[i]=malloc(26*sizeof(Edge));
    	assert(g->edges[i]!=NULL);
    	for(j=0;j<26;j++)
    	{
    		Edge e;
    		e.v='a';        //if no edges exists, the vertex v should be 'a'
    		e.w='a';        //if no edges exists, the vertex w should be 'a'
    		e.delay=0;      //if no edges exists, the delay should be 0
    		e.capacity=0;   //if no edges exists, the capacity should be 0
    		e.count=0;     //if no edges exists, the count should be 0
    		/* make every node in graph is a edge type */
    		g->edges[i][j]=e;
    	}
    }
    return g;
}
void insertEdge(Graph g, Edge e, int i, int j)
{
    assert(g!=NULL);
    if (g->edges[i][j].delay==0)
    {
	    g->edges[i][j]=e;
        g->edges[j][i]=e;
        g->nE++;
    }
}
void freeGraph(Graph g)
{
    assert(g!=NULL);
    int i;
    for (i=0;i<g->nV;i++)
    {
        free(g->edges[i]);
    }
    free(g->edges);
    free(g);
}
