#ifndef MODELS_H_
#define MODELS_H_

using count_type = unsigned long;
#include <random>

extern std::default_random_engine GENERATOR;

inline bool bernoulli(double p){
  return std::bernoulli_distribution(p)(GENERATOR);
}
enum class Progression {
   maternal_immunity = 0,
   susceptible,
   exposed,
   infectious,
   symptomatic,
   severe,
   hospitalised,
   recovered_immune,
   dead
};

enum class VaccinationStatus {
   unvaccinated = 0,
   dose1_given,
   dose2_given
};

struct agent {
  Progression infection_status = Progression::maternal_immunity;
  VaccinationStatus vaccination_status = VaccinationStatus::unvaccinated;
  double time_of_infection = 0;
  bool infective = false;
  int age_in_months = 0;
  int age_index = 0;
  double dose1_time = -1;
  double dose2_time = -1;
  double incubation_period;
  double infectious_period;
  double symptomatic_period;
};

extern double VACCINE_FAILURE_PROB_DOSE1;
extern double VACCINE_FAILURE_PROB_DOSE2;
extern double PROB_SEVERE;
extern double PROB_HOSPITALISED;
extern double PROB_DEATH;

double get_relative_susceptibility(int age_in_months);
#endif