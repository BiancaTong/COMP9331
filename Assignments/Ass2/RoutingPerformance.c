## written by Bianca Tong and Wayne for comp9331 ass2

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "WGraph.h"

char* SHP(Graph,char,char);
char* SDP(Graph,char,char);
char* LLP(Graph,char,char);
typedef struct time_order
{
	double time;
	int index;
	int p_index;
	int operation;
}time_order;
void quick_sort(time_order*,int);
int validpath(Graph,char*,int);
void mark_path(Graph,char*,int);
void release_path(Graph,char**,int*,int);

int main(int argc, char *argv[])
{
	if(argc==6)
	{
		/* read in the topology file */
		FILE* top_file=NULL;
		top_file=fopen(argv[3], "r");
		if(top_file==NULL)
		{
			printf("Unable to open topology file! Exit... \n");
			exit(EXIT_FAILURE);
		}

		/* split the topology file into four list */
		char node1[325];
		char node2[325];
		int delay[325];
		int capacity[325];
		char top_line[12];
		int line_num=0;
		char* delim=" \n";
		while(fgets(top_line,12,top_file)!=NULL)
		{
			int ele_num=0;
			char *top_split=strtok(top_line,delim);
			while(top_split!=NULL)
			{
				if(ele_num==0)
				{
					node1[line_num]=top_split[0];
				}
				else if(ele_num==1)
				{
					node2[line_num]=top_split[0];
				}
				else if(ele_num==2)
				{
					delay[line_num]=atoi(top_split);
				}
				else if(ele_num==3)
				{
					capacity[line_num]=atoi(top_split);
					line_num++;
				}
				top_split=strtok(NULL,delim);
				ele_num++;
			}
		}

		/* transfer node lists into integer form */
		int node1_int[325];
		int node2_int[325];
		int i;
		for(i=0;i<line_num;i++)
		{
			node1_int[i]=node1[i]-'A';
			node2_int[i]=node2[i]-'A';
		}

		/* create a graph */
		Graph topo_graph=createGraph();
		for(i=0;i<325;i++)
		{
			if(node1[i]=='\0')
			{
				break;
			}
			Edge edge;
			edge.v=node1[i];
			edge.w=node2[i];
			edge.delay=delay[i];
			edge.capacity=capacity[i];
			edge.count=0;
			insertEdge(topo_graph,edge,node1_int[i],node2_int[i]);
		}

		/* read in workload file */
		FILE* work_file=NULL;
		work_file=fopen(argv[4], "r");
		if(work_file==NULL)
		{
			printf("Unable to open workload file! Exit... \n");
			exit(EXIT_FAILURE);
		}

		/* split the workload file into four list */
		double start_time[10000];
		char node_source[10000];
		char node_dest[10000];
		double dur_time[10000];
		char work_line[27];
		int line_numm=0;
		while(fgets(work_line,27,work_file)!=NULL)
		{
			char* work_split=NULL;
			int ele_num=0;
			work_split=strtok(work_line,delim);
			while(work_split!=NULL)
			{
				if(ele_num==0)
				{
					start_time[line_numm]=atof(work_split);
				}
				else if(ele_num==1)
				{
					node_source[line_numm]=*work_split;
				}
				else if(ele_num==2)
				{
					node_dest[line_numm]=*work_split;
				}
				else if(ele_num==3)
				{
					dur_time[line_numm]=atof(work_split);
					line_numm++;
				}
				work_split=strtok(NULL,delim);
				ele_num++;
			}
		}

		/* generate a ordered time list for circuit */
		time_order* tt=(time_order*) malloc(2*line_numm*sizeof(time_order));
		for(i=0;i<line_numm;i++)
		{
			tt[i].time=start_time[i];
			tt[i].operation=0;   //request
			tt[i].index=i;
		}
		for(i=line_numm;i<(line_numm*2);i++)
		{
			tt[i].time=start_time[i-line_numm]+dur_time[i-line_numm];
			tt[i].operation=1;   //release
			tt[i].index=i-line_numm;
		}
		quick_sort(tt,line_numm+line_numm);

		int p_rate=atoi(argv[5]);

		/* compute number of packets */
		int packet_num=0;     //sum number of all of the packets
		int *packet_list=(int*)malloc(line_numm*sizeof(int));    //list to store packets num of every line
		for(i=0;i<line_numm;i++)
		{
			int x=(int)(dur_time[i]*p_rate);
			packet_list[i]=x;
			packet_num+=x;
		}

		/* generate a ordered time list for packet */
		time_order* ttt=(time_order*) malloc(2*packet_num*sizeof(time_order));
		int line_index=0;
		int packet_index=0;
		for(i=0;i<packet_num;i++)
		{
			if(packet_index+1<=packet_list[line_index])
			{
				ttt[i].time=start_time[line_index]+(double)(1.0000/p_rate)*packet_index;
				ttt[i].operation=0;   //request
				ttt[i].index=line_index;
				ttt[i].p_index=i;
				packet_index++;
			}
			else
			{
				i=i-1;
				line_index++;
				packet_index=0;
			}
		}
		line_index=0;
		packet_index=0;
		for(i=packet_num;i<(packet_num*2);i++)
		{
			if(packet_index+1<=packet_list[line_index])
			{
				ttt[i].time=start_time[line_index]+(double)(1.0000/p_rate)*(packet_index+1);
				ttt[i].operation=1;   //release
				ttt[i].index=line_index;
				ttt[i].p_index=i;
				packet_index++;
			}
			else
			{
				i=i-1;
				line_index++;
				packet_index=0;
			}
		}
		quick_sort(ttt,2*packet_num);
		free(packet_list);

		/* circuit scheme */
		if(strcmp(argv[1],"CIRCUIT")==0)
		{
			char** sum_path=(char**)malloc(line_numm*sizeof(char*));    //all path list
			for(i=0;i<line_numm;i++)
			{
				sum_path[i]=(char*)malloc(27*sizeof(char));
			}
			int *sum_path_length=(int*)malloc(line_numm*sizeof(int));//all path length list
			int sum_r=0;        //the total number of virtual connection requests
			int sum_total_packects=0; //the total number of packets
			int sum_p=0;        //single packets
			int sum_successful_routes=0;  //the number of successfully routed
			int sum_successful_packects=0;       //the number of successfully routed packets
			int sum_bp=0;       //the number of blocked packets
			int sum_hop=0;      //the number of hops consumed per successfully routed circuit
			int sum_delay=0;    //the number of delay per successfully routed circuit
			for(i=0;i<(2*line_numm);i++)
			{
				//printf("xuhao:%d, caozuo:%d\n", tt[i].index, tt[i].operation);
				if(tt[i].operation==0)
				{
					sum_r++;
					char *route;
					if(strcmp(argv[2],"SHP")==0)
					{
						route=SHP(topo_graph,node_source[tt[i].index],node_dest[tt[i].index]);
						strcpy(sum_path[sum_r-1],route);
					}
					else if(strcmp(argv[2],"SDP")==0)
					{
						route=SDP(topo_graph,node_source[tt[i].index],node_dest[tt[i].index]);
						strcpy(sum_path[sum_r-1],route);
					}
					else if(strcmp(argv[2],"LLP")==0)
					{
						route=LLP(topo_graph,node_source[tt[i].index],node_dest[tt[i].index]);
						strcpy(sum_path[sum_r-1],route);
						//printf("lujing = %s\n", route);
					}
					else
					{
						printf("No such algorithm!!\n");
						exit(EXIT_FAILURE);
					}
					int route_length=0;
					int j;
					for(j=0;j<26;j++)
					{
						if('A'>route[j] || route[j]>'Z')
						{
							route_length=j;
							break;
						}
					}
					sum_path_length[sum_r-1]=route_length;
					if(validpath(topo_graph,route,route_length))
					{
						sum_successful_routes++;
						mark_path(topo_graph,route,route_length);
						sum_hop=sum_hop+(route_length-1);

						for(j=0;j<route_length-1;j++)
						{
							int node_s=route[j]-'A';
							int node_d=route[j+1]-'A';
							sum_delay=sum_delay+topo_graph->edges[node_s][node_d].delay;
						}
						//printf("sumdelay=%d\n", sum_delay);
					}
					else
					{
						sum_p=(int)(dur_time[tt[i].index]*p_rate);
						sum_bp+=sum_p;
						char* path_null="";
						sum_path[sum_r-1]=path_null;
					}
					free(route);
				}
				else      //release
				{
					sum_p=(int)(dur_time[tt[i].index]*p_rate);
					char* com="";
					if(strcmp(sum_path[tt[i].index],com)!=0)
					{
						release_path(topo_graph,sum_path,sum_path_length,tt[i].index);
						sum_successful_packects+=sum_p;
					}
					sum_total_packects+=sum_p;
				}
			}
			free(sum_path);
			free(sum_path_length);
			printf("total number of virtual connection requests: %d\n",sum_r);
			printf("total number of packets: %d\n",sum_total_packects);
			printf("number of successfully routed packets: %d\n",sum_successful_packects);
			printf("percentage of successfully routed packets: %.2f\n",(double)((double)sum_successful_packects/(double)sum_total_packects*(double)100.00));
			printf("number of blocked packets: %d\n",sum_bp);
			printf("percentage of blocked packets: %.2f\n",(double)((double)sum_bp/(double)sum_total_packects*(double)100.00));
			printf("average number of hops per circuit: %.2f\n",(double)((double)sum_hop/(double)sum_successful_routes));
			printf("average cumulative propagation delay per circuit: %.2f\n",(double)((double)sum_delay/(double)sum_successful_routes));
		}

		/* packet scheme */
		if(strcmp(argv[1],"PACKET")==0)
		{
			char** sum_path=(char**)malloc(packet_num*sizeof(char*));    //all path list
			int i;
			for(i=0;i<packet_num;i++)
			{
				sum_path[i]=(char*)malloc(27*sizeof(char));
			}
			int *sum_path_length=(int*)malloc(packet_num*sizeof(int));//all path length list
			int sum_total_packects=0; //the total number of packets
			int sum_successful_packects=0;       //the number of successfully routed packets
			int sum_bp=0;       //the number of blocked packets
			int sum_hop=0;      //the number of hops consumed per successfully routed packets
			int sum_delay=0;    //the number of delay per successfully routed packets
			for(i=0;i<(2*packet_num);i++)
			{
				if(ttt[i].operation==0)
				{
					sum_total_packects++;
					char *route;
					if(strcmp(argv[2],"SHP")==0)
					{
						route=SHP(topo_graph,node_source[ttt[i].index],node_dest[ttt[i].index]);
						strcpy(sum_path[ttt[i].p_index],route);
					}
					else if(strcmp(argv[2],"SDP")==0)
					{
						route=SDP(topo_graph,node_source[ttt[i].index],node_dest[ttt[i].index]);
						strcpy(sum_path[ttt[i].p_index],route);
					}
					else if(strcmp(argv[2],"LLP")==0)
					{
						route=LLP(topo_graph,node_source[ttt[i].index],node_dest[ttt[i].index]);
						strcpy(sum_path[ttt[i].p_index],route);
					}
					else
					{
						printf("No such algorithm!!\n");
						exit(EXIT_FAILURE);
					}
					int route_length=0;
					int j;
					for(j=0;j<26;j++)
					{
						if('A'>route[j] || route[j]>'Z')
						{
							route_length=j;
							break;
						}
					}
					sum_path_length[ttt[i].p_index]=route_length;
					if(validpath(topo_graph,route,route_length))
					{
						sum_successful_packects++;
						mark_path(topo_graph,route,route_length);
						sum_hop=sum_hop+(route_length-1);
						for(j=0;j<route_length-1;j++)
						{
							int node_s=route[j]-'A';
							int node_d=route[j+1]-'A';
							sum_delay=sum_delay+topo_graph->edges[node_s][node_d].delay;
						}
					}
					else
					{
						sum_bp++;
						char* path_null="";
						sum_path[ttt[i].p_index]=path_null;
					}
					free(route);
				}
				else      //release
				{
					char* com="";
					if(strcmp(sum_path[ttt[i].p_index-packet_num],com)!=0)
					{
						release_path(topo_graph,sum_path,sum_path_length,ttt[i].p_index-packet_num);
					}
				}
			}
			free(sum_path);
			free(sum_path_length);
			printf("total number of virtual connection requests: %d\n",line_numm);
			printf("total number of packets: %d\n",sum_total_packects);
			printf("number of successfully routed packets: %d\n",sum_successful_packects);
			printf("percentage of successfully routed packets: %.2f\n",(double)((double)sum_successful_packects/(double)sum_total_packects*(double)100.00));
			printf("number of blocked packets: %d\n",sum_bp);
			printf("percentage of blocked packets: %.2f\n",(double)((double)sum_bp/(double)sum_total_packects*(double)100.00));
			printf("average number of hops per circuit: %.2f\n",(double)((double)sum_hop/(double)sum_successful_packects));
			printf("average cumulative propagation delay per circuit: %.2f\n",(double)((double)sum_delay/(double)sum_successful_packects));
		}
		free(tt);
		free(ttt);
		freeGraph(topo_graph);
		fclose(top_file);
		fclose(work_file);
	}
	else
	{
		printf("Not valid input. Exit... \n");
		exit(EXIT_FAILURE);
	}
	return 0;
}

/* quick sort */
void quick_sort(time_order *a,int n)
{
    int i,j;
    time_order p,tmp;
    if (n<2) return;
    p=a[n/2];
    for (i=0,j=n-1;;i++,j--)
    {
        while (a[i].time<p.time || (a[i].time==p.time && a[i].operation==1 && p.operation==0))
            i++;
        while (p.time<a[j].time || (a[j].time==p.time && a[j].operation==0 && p.operation==1))
            j--;
        if (i>=j)
            break;
        tmp=a[i];a[i]=a[j];a[j]=tmp;
     }
    quick_sort(a,i);
    quick_sort(a+i,n-i);
}

/* check block */
int validpath(Graph g,char* path,int l)
{
	int i;
	for(i=0;i<l-1;i++)
	{
		int node_s=path[i]-'A';
		int node_d=path[i+1]-'A';
		if(g->edges[node_s][node_d].count>=g->edges[node_s][node_d].capacity ||
				g->edges[node_d][node_s].count>=g->edges[node_d][node_s].capacity)
		{
			return 0;
		}
	}
	return 1;
}

/* mark count */
void mark_path(Graph g,char* path,int l)
{
	int i;
	for(i=0;i<l-1;i++)
	{
		int node_s=path[i]-'A';
		int node_d=path[i+1]-'A';
		g->edges[node_s][node_d].count++;
		g->edges[node_d][node_s].count++;
	}
}

/* release count */
void release_path(Graph g,char** s,int* l,int index)
{
	int i;
	for(i=0;i<l[index]-1;i++)
	{
		int node_s=s[index][i]-'A';
		int node_e=s[index][i+1]-'A';
		g->edges[node_s][node_e].count--;
		g->edges[node_e][node_s].count--;
	}
}

/* SHP algorithm */
char* SHP(Graph g,char source,char dest)
{
	int* pre_node=malloc(26*sizeof(int));   //marked the pre node of every node
	int* visited=malloc(26*sizeof(int));    //visited node marked
	int* dist=malloc(26*sizeof(int));       //distance from source node, unknown is -1
	int source_int=source-'A';
	int dest_int=dest-'A';
	time_t t;
	srand((unsigned)time(&t));     //set seed for random
	int i;
	
	for(i=0;i<26;i++)
	{
		pre_node[i]=-1;
		dist[i]=-1;
		visited[i]=-1;
	}
	dist[source_int]=0;
	pre_node[source_int]=source_int;

	while(1)
	{
		int min=26;
		int min_index=0;
		for(i=0;i<26;i++)
		{
			if(dist[i]<=min && visited[i]==-1 && dist[i]>=0)
			{
				if(dist[i]==min)
				{
					double r = (double)(10.0*rand() / (RAND_MAX + 1.0));   //get random number
					if(r>=5)
					{
						min=dist[i];
						min_index=i;
					}
				}
				else
				{
					min=dist[i];
					min_index=i;
				}
			}
		}

		if (dist[dest_int] == min && dist[dest_int] >= 0)
		{
			min = dist[dest_int];
			min_index = dest_int;
			break;
		}

		for(i=0;i<26;i++)
		{
			if(g->edges[min_index][i].delay!=0 && visited[i]==-1)
			{
				if(dist[i]>(dist[min_index]+1))
				{
					dist[i]=dist[min_index]+1;
					pre_node[i]=min_index;
				}
				else if(dist[i]==-1)
				{
					dist[i]=dist[min_index]+1;
					pre_node[i]=min_index;
				}
			}
		}
		visited[min_index]=1;
		if(visited[dest_int]==1)
		{
			break;
		}
	}
	char* path=malloc(27*sizeof(char));
	int length=0;
	for(i=0;i<26;i++)
	{
		if(i==0)
		{
			path[i]=dest;
		}
		else
		{
			int index=path[i-1]-'A';
			path[i]=pre_node[index]+'A';
		}
		if(path[i]==source)
		{
			path[i+1]='\0';
			length=i+2;
			break;
		}
	}
	char* path_r=malloc(length*sizeof(char));
	for(i=0;i<length;i++)
	{
		if(i<length-1)
		{
			path_r[i]=path[length-i-2];
		}
		else
		{
			path_r[i]='\0';
		}
	}
	free(visited);
	free(dist);
	free(pre_node);
	free(path);
	return(path_r);
}

/* SDP algorithm */
char* SDP(Graph g,char source,char dest)
{
	int* pre_node=malloc(26*sizeof(int));   //marked the pre node of every node
	int* visited=malloc(26*sizeof(int));    //visited node marked
	int* dist=malloc(26*sizeof(int));       //distance from source node, unknown is -1
	int source_int=source-'A';
	int dest_int=dest-'A';
	time_t t;
	srand((unsigned)time(&t));     //set seed for random
	int i;
	
	for(i=0;i<26;i++)
	{
		pre_node[i]=-1;
		dist[i]=-1;
		visited[i]=-1;
	}
	dist[source_int]=0;
	pre_node[source_int]=source_int;

	while(1)
	{
		int min=5200;
		int min_index=0;
		for(i=0;i<26;i++)
		{
			if(dist[i]<=min && visited[i]==-1 && dist[i]>=0)
			{
				if(dist[i]==min)
				{
					double r = (double)(10.0*rand() / (RAND_MAX + 1.0));   //get random number
					if(r>=5)
					{
						min=dist[i];
						min_index=i;
					}
				}
				else
				{
					min=dist[i];
					min_index=i;
				}
			}
		}

		if (dist[dest_int] == min && dist[dest_int] >= 0)
		{
			min = dist[dest_int];
			min_index = dest_int;
			break;
		}

		for(i=0;i<26;i++)
		{
			if(g->edges[min_index][i].delay!=0 && visited[i]==-1)
			{
				if(dist[i]>(dist[min_index]+g->edges[min_index][i].delay))
				{
					dist[i]=dist[min_index]+g->edges[min_index][i].delay;
					pre_node[i]=min_index;
				}
				else if(dist[i]==-1)
				{
					dist[i]=dist[min_index]+g->edges[min_index][i].delay;
					pre_node[i]=min_index;
				}
			}
		}
		visited[min_index]=1;
		if(visited[dest_int]==1)
		{
			break;
		}
	}
	char* path=malloc(27*sizeof(char));
	int length=0;
	for(i=0;i<26;i++)
	{
		if(i==0)
		{
			path[i]=dest;
		}
		else
		{
			int index=path[i-1]-'A';
			path[i]=pre_node[index]+'A';
		}
		if(path[i]==source)
		{
			path[i+1]='\0';
			length=i+2;
			break;
		}
	}
	char* path_r=malloc(length*sizeof(char));
	for(i=0;i<length;i++)
	{
		if(i<length-1)
		{
			path_r[i]=path[length-i-2];
		}
		else
		{
			path_r[i]='\0';
		}
	}
	free(visited);
	free(dist);
	free(pre_node);
	free(path);
	return(path_r);
}

/* LLP algorithm */
char* LLP(Graph g,char source,char dest)
{
	int* pre_node=malloc(26*sizeof(int));   //marked the pre node of every node
	int* visited=malloc(26*sizeof(int));    //visited node marked
	double* dist=malloc(26*sizeof(double));       //distance from source node, unknown is -1
	int source_int=source-'A';
	int dest_int=dest-'A';
	time_t t;
	srand((unsigned)time(&t));     //set seed for random
	int i;
	
	for(i=0;i<26;i++)
	{
		pre_node[i]=-1;
		dist[i]=-1.00;
		visited[i]=-1;
	}
	dist[source_int]=0.00;
	pre_node[source_int]=source_int;

	while(1)
	{
		double min=1.00;
		int min_index=0;
		for(i=0;i<26;i++)
		{
			if(dist[i]<=min && visited[i]==-1 && dist[i]>=0)
			{
				if(dist[i]==min)
				{
					double r = (double)(10.0*rand() / (RAND_MAX + 1.0));   //get random number
					if(r>=5)
					{
						min=dist[i];
						min_index=i;
					}
				}
				else
				{
					min=dist[i];
					min_index=i;
				}
			}
		}
		if (dist[dest_int] == min && dist[dest_int]>=0)
		{
			min = dist[dest_int];
			min_index = dest_int;
			break;
		}

		for(i=0;i<26;i++)
		{
			if(g->edges[min_index][i].delay!=0 && visited[i]==-1)
			{
				double dist_i=((double)g->edges[min_index][i].count)/((double)g->edges[min_index][i].capacity);
				if(dist[i]>(dist[min_index]+dist_i))
				{
					dist[i]=dist[min_index]+dist_i;
					pre_node[i]=min_index;
				}
				else if(dist[i]==-1)
				{
					dist[i]=dist_i;
					pre_node[i]=min_index;
				}
			}
		}
		visited[min_index]=1;
		if(visited[dest_int]==1)
		{
			break;
		}
	}
	char* path=malloc(27*sizeof(char));
	int length=0;
	for(i=0;i<26;i++)
	{
		if(i==0)
		{
			path[i]=dest;
		}
		else
		{
			int index=path[i-1]-'A';
			path[i]=pre_node[index]+'A';
		}
		if(path[i]==source)
		{
			path[i+1]='\0';
			length=i+2;
			break;
		}
	}
	char* path_r=malloc(length*sizeof(char));
	for(i=0;i<length;i++)
	{
		if(i<length-1)
		{
			path_r[i]=path[length-i-2];
		}
		else
		{
			path_r[i]='\0';
		}
	}
	free(visited);
	free(dist);
	free(pre_node);
	free(path);
	return(path_r);
}
