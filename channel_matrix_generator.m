
trajectory = dlmread('channel4.csv');
[chanStates,rates] = kmeans(trajectory',4);
rates = sort(rates);
for i = 1:length(chanStates)
    if abs(trajectory(i) - rates(1)) < abs(trajectory(i) - rates(2)) && ...
            abs(trajectory(i) - rates(1)) < abs(trajectory(i) - rates(3)) && abs(trajectory(i) - rates(1)) < abs(trajectory(i) - rates(4))
       chanStates(i) = 1;     
    elseif abs(trajectory(i) - rates(2)) < abs(trajectory(i) - rates(1)) && ...
            abs(trajectory(i) - rates(2)) < abs(trajectory(i) - rates(3)) && abs(trajectory(i) - rates(2)) < abs(trajectory(i) - rates(4))
       chanStates(i) = 2;
    elseif abs(trajectory(i) - rates(3)) < abs(trajectory(i) - rates(1)) && ...
            abs(trajectory(i) - rates(3)) < abs(trajectory(i) - rates(2)) && abs(trajectory(i) - rates(3)) < abs(trajectory(i) - rates(4))
       chanStates(i) = 3;
    elseif abs(trajectory(i) - rates(4)) < abs(trajectory(i) - rates(1)) && ...
         abs(trajectory(i) - rates(4)) < abs(trajectory(i) - rates(2)) && abs(trajectory(i) - rates(4)) < abs(trajectory(i) - rates(3))
       chanStates(i) = 4;     
    end
end

chanMat = zeros(4,4);
for i = 1:4
    sum = 0;
    sumDest = zeros(1,4);
    for s = 1:length(chanStates)-1
        if chanStates(s) == i
            sum = sum + 1;
            for j = 1:4
                 if chanStates(s + 1) == j
                    sumDest(j) = sumDest(j) + 1;
                 end
            end
        end
    end
    chanMat(i,:) = sumDest / sum;
end
chanMat
         