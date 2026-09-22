#include "models.h"

std::default_random_engine GENERATOR;
double VACCINE_FAILURE_PROB_DOSE1;
double VACCINE_FAILURE_PROB_DOSE2;
double PROB_SEVERE;
double PROB_HOSPITALISED;
double PROB_DEATH;
//An age-stratified mathematical model to inform optimal measles vaccination strategies(https://www.medrxiv.org/content/10.1101/2025.04.01.25325066v1.full.pdf)

double get_relative_susceptibility(int age_in_months){
  if(age_in_months < 3){
    return 0.2;   // α2(1)
  } else if(age_in_months < 6){
    return 0.6;   // α2(2)
  } else if(age_in_months < 9){
    return 1.0;   // α2(3)
  } else {
    return 0.0;   // α2(i) = 0 for i = 4 and above
  }
}