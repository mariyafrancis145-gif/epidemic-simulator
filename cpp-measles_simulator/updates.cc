#include <algorithm>
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <unordered_map>

#include "updates.h"

void init_agent_disease_state(agent& node){
  // TODO: replace fixed values with sampling from real distributions
  // once transition-time data is gathered (e.g. gamma-distributed,
  // matching the reference file's pattern).
  node.incubation_period = 0;
  node.infectious_period = 0;
  node.symptomatic_period = 0;
}

bool check_exposure(const agent& node){
  // TODO: depends on force-of-infection / lambda functions —
  // separate body of work, not yet built.
  return false;
}

node_update_status update_infection(agent& node, double cur_time){
  node_update_status update_status;

    if(node.infection_status == Progression::maternal_immunity){
    if(node.age_in_months >= 9){
      // α2(i) = 0 for i = 4 and above (9+ months) — fully out of the
      // maternal-immune class, per Table 2, medRxiv 2025.04.01.25325066.
      node.infection_status = Progression::susceptible;
    }
    else if(check_exposure(node)){
      double susceptibility = get_relative_susceptibility(node.age_in_months);
      if(bernoulli(susceptibility)){
        node.infection_status = Progression::exposed;
        node.time_of_infection = cur_time;
        update_status.new_infection = true;
      }
    }
  }

  else if(node.infection_status == Progression::susceptible){
    bool exposure_occurs = check_exposure(node);

    if(exposure_occurs){
      bool blocked_by_vaccine = false;
      if(node.vaccination_status == VaccinationStatus::dose2_given){
        blocked_by_vaccine = !bernoulli(VACCINE_FAILURE_PROB_DOSE2);
      } else if(node.vaccination_status == VaccinationStatus::dose1_given){
        blocked_by_vaccine = !bernoulli(VACCINE_FAILURE_PROB_DOSE1);
      }
      if(!blocked_by_vaccine){
        node.infection_status = Progression::exposed;
        node.time_of_infection = cur_time;
        update_status.new_infection = true;
      }
    }
  }

  else if(node.infection_status == Progression::exposed
          && (cur_time - node.time_of_infection > node.incubation_period)){
    node.infection_status = Progression::infectious;
    node.infective = true;
    update_status.new_infective = true;
  }

  else if(node.infection_status == Progression::infectious
          && (cur_time - node.time_of_infection
              > node.incubation_period + node.infectious_period)){
    node.infection_status = Progression::symptomatic;
  }

  else if(node.infection_status == Progression::symptomatic
          && (cur_time - node.time_of_infection
              > node.incubation_period + node.infectious_period + node.symptomatic_period)){
    if(bernoulli(PROB_SEVERE)){
      node.infection_status = Progression::severe;
      update_status.new_severe = true;
    } else {
      node.infection_status = Progression::recovered_immune;
      node.infective = false;
    }
  }

  else if(node.infection_status == Progression::severe){
    if(bernoulli(PROB_HOSPITALISED)){
      node.infection_status = Progression::hospitalised;
      update_status.new_hospitalization = true;
    } else {
      node.infection_status = Progression::recovered_immune;
      node.infective = false;
    }
  }

  else if(node.infection_status == Progression::hospitalised){
    if(bernoulli(PROB_DEATH)){
      node.infection_status = Progression::dead;
      update_status.new_death = true;
    } else {
      node.infection_status = Progression::recovered_immune;
      node.infective = false;
    }
  }

  return update_status;
}