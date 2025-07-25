import numpy as np
import matplotlib . pyplot as plt
import random
import math
import pandas as pd
import scipy.stats as stat
import scipy.optimize as opt


#parámetro de forma     
def gamma_alpha_i(theta, s1, s2):
  a0 = theta[0]
  a1 = theta[1]
  a2 = theta[2]
  alphai =[]
  for i in s1:
      for j in s2:
          alphai.append( np.exp(a0 + a1*i +a2*j))
  return np.array(alphai)

#parámetro de escala
def gamma_lambda_i(theta, s1, s2):
  b0 = theta[3]
  b1 = theta[4]
  b2 = theta[5]
  lambdai = []
  for i in s1:
      for j in s2:
          lambdai.append(np.exp(b0 + b1*i +b2*j))
  return np.array(lambdai)

#print(gamma_alpha_i(theta_0_gamma, s1_gamma, s2_gamma))
#print(gamma_lambda_i(theta_0_gamma, s1_gamma, s2_gamma))
#Funcion de distribución gamma
def gamma_distribucion(t, theta, s1, s2):
  alphai = gamma_alpha_i(theta, s1, s2)
  lambdai = gamma_lambda_i(theta, s1, s2)
  return stat.gamma.cdf(t, alphai, scale = lambdai)
    
#Cálculo de probabilidad de fallo en el el momento de inspección IT_i
def probabilidad_gamma(theta, IT, s1, s2):
  probabilidades1 = []
  for l in range(len(IT)):
    probabilidades1.extend(gamma_distribucion(IT[l], theta, s1 , s2))
  return np.array(probabilidades1)

#print(probabilidad_gamma_sin_contaminar(theta_0_gamma, IT_gamma, s1_gamma, s2_gamma))

#Generación de la muestra 
def gen_muestra_binomial_gamma(theta_0, IT, s1, s2, K, seed):
  n_i =  []
  pi_theta1 = probabilidad_gamma(theta_0, IT, s1, s2)
  np.random.seed(seed)
  for i in range(len(pi_theta1)):
        n_i.append(np.random.binomial(K, pi_theta1[i]))
  return np.array(n_i)

#Cálculo del vector de probabilidades de fallo para la muestra
def probabilidad_estimada(muestra, K):
  p1 = []
  p2 = []
  for i in range(len(muestra)):
    p1.append(muestra[i]/K)
    p2.append(1 - muestra[i]/K)
  return np.array(p1)

#Divergencia de Kullback-Leibler
def divergencia_KL(pi_theta1, pi_theta2, p1, p2, theta, IT, s1, s2, muestra, K):
  pi_theta1 = probabilidad_gamma(theta, IT, s1, s2)
  pi_theta2 = 1 - pi_theta1
  p1 = probabilidad_estimada(muestra, K)
  p2 = 1 - p1
  div_KL = []
  
  eps = 1e-10
  
  pi_theta1 = np.where(pi_theta1 == 0, eps, pi_theta1)
  pi_theta2 = np.where(pi_theta2 == 0, eps, pi_theta2)
  p1 = np.where(p1 == 0, eps, p1)
  p2 = np.where(p2 == 0, eps, p2)

  for i in range(len(muestra)):
      div_KL.append(K*((p1[i]* np.log(p1[i]/pi_theta1[i])) + (p2[i]* np.log(p2[i]/pi_theta2[i]))))
  return np.array(div_KL)

#Divergencia de densidad de potencia en función del parámetro alpha
def divergencia_gamma(theta, alpha, IT, s1, s2, K, muestra):
  pi_theta1 = probabilidad_gamma(theta, IT, s1, s2)
  pi_theta2 = 1 - pi_theta1
  p1 = probabilidad_estimada(muestra, K)
  p2 = 1 - p1
  K_total = len(muestra)*K
  div_alpha = []
  
  if alpha == 0:
    for i in range(len(muestra)) :
        div = divergencia_KL(pi_theta1, pi_theta2, p1, p2, theta, IT, s1, s2, muestra, K)
        div_alpha.append(div)
 
  else:
    for i in range(len(muestra)) :
        div_alpha.append(K*((pi_theta1[i]**(1+ alpha) + pi_theta2[i]**(1+ alpha)) - (1 + 1/alpha)*((p1[i])*(pi_theta1[i])**alpha + (p2[i])*(pi_theta2[i])**alpha)))
  
  div_alpha_pond = (np.sum(div_alpha))/K_total
  return div_alpha_pond

#Cálculo del EMDP
def emdp(theta_inicial, alpha, IT, s1, s2, K, muestra):
  args = (alpha, IT, s1,s2, K,  muestra)
  #bounds = [(5, 5.6),(-0.1, 1e-3), (-1, 1e-3),(-0.1, 1e-3)]
  #bounds = [(1e-3, None),(None, -1e-3),(None, -1e-3),(None, -1e-3),(1e-3, None),(None, -1e-3)]
  #6.5, -0.06,-0.06, -0.5, 0.065,-0.01
  estimador = opt.minimize(divergencia_gamma, theta_inicial, args=args,  method = 'Nelder-Mead') # #L-BFGS-BNelder-Mead # bounds = bounds,
  return estimador.x


#Simulación

def simulacion(R, theta_0, theta_inicial, theta_cont, IT,s1,s2, K, alphas):
    #Se simula una muestra sin contaminar y una muestra contaminada en función de un parámetro theta contaminado para la primera celda
    #Devuelve el EMDP para la muestra sin contaminar y para la muestra contaminada, así como el RMSE de ambos estimadores.
    
    media_estimador =[]
    media_estimador_cont = []
    rmse_values = []
    rmse_cont_values = []
    
    for alpha in alphas:
      estimador = []
      estimador_cont = []
      
      for j in range(R):
          
        #Se estima el valor del emdp para la muestra sin contaminar  
        muestra = gen_muestra_binomial_gamma(theta_0, IT, s1, s2, K, j)
        theta_estimador = emdp(theta_inicial, alpha, IT, s1, s2, K, muestra)
        estimador.append(theta_estimador)
        
        #Se estima el valor del emdp para la muestra contaminada
        muestra_cont = gen_muestra_binomial_gamma(theta_cont, IT, s1, s2, K, j)
        muestra[0] = muestra_cont[0]
        theta_estimador_cont = emdp(theta_inicial, alpha, IT, s1, s2, K, muestra)
        estimador_cont.append(theta_estimador_cont)

        #Se ecalcula la media del emdp sin contaminar
      mean_estimator = np.mean(estimador, axis = 0)
      mean_estimator_cont = np.mean(estimador_cont, axis = 0)
      
      #Se calcula la media del emdp contaminado
      media_estimador.append(mean_estimator)
      media_estimador_cont.append(mean_estimator_cont)

        #Cálculo del RMSE para la muestra sin contaminar
      mse = np.mean((theta_0 - mean_estimator) ** 2)
      rmse = np.sqrt(mse)
      rmse_values.append(rmse)

        #Cálculo del RMSE para la muestra contamindada
      mse_cont = np.mean((theta_0 - mean_estimator_cont) ** 2)
      rmse_cont = np.sqrt(mse_cont)
      rmse_cont_values.append(rmse_cont)

   # Convertir a DataFrames
    df_estimators = pd.DataFrame(media_estimador, columns=[f"param_{i+1}" for i in range(len(theta_0))])
    df_estimators["alpha"] = alphas
    df_estimators_cont = pd.DataFrame(media_estimador_cont, columns=[f"param_cont_{i+1}" for i in range(len(theta_0))])
    df_estimators_cont["alpha"] = alphas

    df_rmse = pd.DataFrame({"alpha": alphas, "rmse": rmse_values, "rmse_cont": rmse_cont_values})

    # Guardar en CSV
    df_estimators.to_csv("estimators.csv", index=False)
    df_estimators_cont.to_csv("estimators_cont.csv", index=False)
    df_rmse.to_csv("rmse.csv", index=False)
    print("CSV files saved: 'estimators.csv', 'estimators_cont.csv', and 'rmse.csv'")
    return np.array(media_estimador), np.array(media_estimador_cont), np.array(rmse_values), np.array(rmse_cont_values)


R= 1000
IT_gamma = np.array([16,24,32])
K = 100
s1_gamma = np.array([30,40])
s2_gamma = np.array([40,50])
#theta_0_gamma = np.array([4.5, -0.065, -0.46, 0.05])
theta_0_gamma = np.array([6.5, -0.06,-0.06, -0.5, 0.065,-0.01])
#theta_inicial_gamma = np.array([4.40, -0.065 ,-0.46, 0.05])
theta_inicial_gamma = np.array([6.3, -0.065,-0.06, -0.5, 0.065,-0.01])
#theta_cont_gamma = np.array([4.5, -0.07 ,-0.46, 0.05])
theta_cont_gamma = np.array([6.5, -0.045,-0.06, -0.5, 0.065,-0.01])
alphas= np.array([0, 0.2, 0.4, 0.6, 0.8, 1])

media_estimador_gamma, media_estimador_cont_gamma, rmse_values_gamma, rmse_cont_values_gamma = simulacion(R,theta_0_gamma, theta_inicial_gamma, theta_cont_gamma, IT_gamma, s1_gamma, s2_gamma, K, alphas)

#Cálculo de la fiabilidad


IT1 = np.array([10,20,30])


s_prueba = [25,30]

def distribucion1(t, theta,s): #Función de distribucion gamma

  a0 = theta[0]
  a1 = theta[1]
  a2 = theta[2]
  b0 = theta[3]
  b1 = theta[4]
  b2 = theta[5]
  
  lambdai =np.exp(a0 + a1*s_prueba[0]+a2*s_prueba[1])
  sigmai =np.exp(b0 + b1*s_prueba[0]+b2*s_prueba[1])

  return stat.gamma.cdf(t, sigmai, scale = lambdai)

def fiabilidad(theta, IT, s): #Probabilidad de fallo para cada intervalo


  probabilidades1 = []
  probabilidades2 = []

  for l in range(len(IT)):

    probabilidades1.append(distribucion1(IT[l], theta, s))
    probabilidades2.append(1 - distribucion1(IT[l], theta, s))


  return np.array(probabilidades2)

lista_probs = fiabilidad(theta_0_gamma, IT1, s_prueba)

df = pd.read_csv("C:/Users/J.ESPLUGUESGARCIA/OneDrive - Zurich Insurance/Uni/TFG_matematicas_Code/gamma/estimators.csv")  # Replace with the actual CSV file path
results_list = []

for index, row in df.iterrows():
    theta = row[0:6].values  # Extract the 4 estimated parameters from each row
    alpha_value = row.iloc[-1]  # Extract alpha value

    prob_vector = fiabilidad(theta, IT1, s_prueba)  # Compute fiabilidad function

    # Store results in a dictionary format
    results_list.append([alpha_value] + prob_vector.tolist())

columns = ["alpha"] + [f"R{IT1[i]}" for i in range(len(IT1))]
columnas = [f"R{IT1[i]}" for i in range(len(IT1))]
results_df1 = pd.DataFrame(results_list, columns=columns)
for i, col in enumerate(columnas):
    results_df1[col] = results_df1[col] - lista_probs[i]
# Step 6: Save results to a separate CSV file
results_df1.to_csv("fiabilidad_results.csv", index=False)

# Print confirmation
print("Results saved in 'fiabilidad_results.csv'.")

df = pd.read_csv("C:/Users/J.ESPLUGUESGARCIA/OneDrive - Zurich Insurance/Uni/TFG_matematicas_Code/gamma/estimators_cont.csv")  # Replace with the actual CSV file path
results_list = []

for index, row in df.iterrows():
    theta = row[0:6].values  # Extract the 4 estimated parameters from each row
    alpha_value = row.iloc[-1]  # Extract alpha value

    prob_vector = fiabilidad(theta, IT1, s_prueba)  # Compute fiabilidad function

    # Store results in a dictionary format
    results_list.append([alpha_value] + prob_vector.tolist())

columns = ["alpha"] + [f"R{IT1[i]}" for i in range(len(IT1))]
columnas = [f"R{IT1[i]}" for i in range(len(IT1))]
results_df2 = pd.DataFrame(results_list, columns=columns)
for i, col in enumerate(columnas):
    results_df2[col] = results_df2[col] - lista_probs[i]


# Step 6: Save results to a separate CSV file
results_df2.to_csv("fiabilidad_results_cont.csv", index=False)

df2_sin_primera = results_df2.iloc[:, 1:]

# Print confirmation
print("Results saved in 'fiabilidad_results_cont.csv'.")




df_combinado = pd.concat([results_df1, df2_sin_primera], axis=1)
latex_table=df_combinado.to_latex(index=False)
df_rmse = pd.read_csv("C:/Users/J.ESPLUGUESGARCIA/OneDrive - Zurich Insurance/Uni/TFG_matematicas_Code/gamma/rmse.csv")
tabla_latex_rmse = df_rmse.to_latex(index=False)

# Print 
print(latex_table)

print(tabla_latex_rmse)
