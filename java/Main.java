import android.os.Debug;
import com.example.cars.CarExample;
import com.example.shadowing.ShadowingExample;

public class Main {
	public static void main(String[] args) {
		Object[] examples = new Object[3];

		examples[0] = new CarExample();
		examples[1] = null;
		examples[2] = new ShadowingExample();

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
