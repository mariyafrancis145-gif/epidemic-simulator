#ifndef UPDATES_H_
#define UPDATES_H_

#include "models.h"

struct node_update_status {
  bool new_infection = false;
  bool new_infective = false;
  bool new_severe = false;
  bool new_hospitalization = false;
  bool new_death = false;
};

node_update_status update_infection(agent& node, double cur_time);
void init_agent_disease_state(agent& node);
bool check_exposure(const agent& node);

#endif