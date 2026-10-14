# Row216 Bayesian Optimization

Exact description: "Efficiently searches parameter space".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Native standalone exact rational finite-function Bayesian optimization suggests
one unobserved candidate using expected latent improvement. Caller supplies
finite hypotheses/priors/objective values per candidate, observations and Cauchy
noise scale. Sequential exact Bayes normalization, posteriorhistory/means/
variances/EI,observedincumbent,min/max,tiescandidateorder. No objectiveevaluation
executed. DifferentfromgenericGaussianprocesscontinuousoptimizer,scopeexplicit.

Caps2..20candidateIDs/1..20hypotheses/1..20observations/80charuniqueIDs/values
+-1000/prior0..1exactsum1/noisescale1e-6..1000. Repeatedobservationsallowed,
zero-priorhypothesisstayszero,atleastoneunobservedcandidate. Strictschema/types/
rangebeforeconversionincludinghugeints/capsbeforescan/no mutation.
Fourtests400independentjoint-likelihoodexactposterior/acquisitionoracles,
asymmetrichandmeanvarianceEI/minmax/zeroprior/repeatedobs/allcaps/refusals.
Broad70/70ownASTkills. WorkfiniteO(hypotheses*(observations+candidates)).

SCOPED finitehypothesisBayesacquisition,literalPARTIAL. NOT_CLAIMED continuous
optimization,authenticprior/noise,trueparameter-spaceefficiency/globaloptimum/
realobjectiveexecution/runtimeintegration. EIlimitedtosuppliedhypotheses;
posteriorcertaintycanbefalsewhenmodelmisspecified. Unitscaller-supplied.
Native namespaceimport/newfilesonly/noinit,claimexclusive216. Audit required.
