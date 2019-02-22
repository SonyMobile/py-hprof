import com.example.Car;
import com.example.Bike;
import android.os.Debug;

public class Main {
	private static Object bikeSuper;
	private static String nothing = "not yet nothing";

	public static void main(String[] args) {
		nothing = null;

		Object[] objs = new Object[] {
			new Car("Lolvo"),
			new Car("Yotoya"),
			new Bike("Fånark"),
			new Car("Bowie"),
			new Bike("Descent")
		};

		bikeSuper = objs[4].getClass();

		if (args.length > 0) {
			Debug.dumpHprofData(args[0]);
		} else {
			long end = System.currentTimeMillis() + 10000;
			while (System.currentTimeMillis() < end) {
				try {
					Thread.sleep(1);
				} catch (InterruptedException e) {
					// just sleep more.
				}
			}
		}
	}
}
